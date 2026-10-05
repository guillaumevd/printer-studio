import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.desktop import updater
from app.desktop.startup import Startup, SplashAPI


class UpdateTests(unittest.TestCase):
    def release(self):
        name = 'PrinterStudio-Setup-1.4.1-x64.exe'
        asset = dict(name=name, size=3, browser_download_url=f'https://github.com/{updater.REPOSITORY}/releases/download/v1.4.1/{name}')
        return dict(tag_name='v1.4.1', draft=False, prerelease=False, assets=[asset]), dict(version='1.4.1', filename=name, size=3, sha256=hashlib.sha256(b'abc').hexdigest())

    def test_numeric_versions_and_invalid_tags(self):
        self.assertGreater(updater.version_tuple('1.10.0'), updater.version_tuple('v1.9.9'))
        for value in ('latest', '../1.4.1', '1.4.1-beta', None):
            with self.assertRaises(ValueError): updater.version_tuple(value)

    def test_manifest_integrity_and_repository_scope(self):
        release, manifest = self.release()
        self.assertEqual(updater.validate_manifest(release, manifest)['version'], '1.4.1')
        release['assets'][0]['browser_download_url'] = 'https://example.org/installer.exe'
        with self.assertRaises(ValueError): updater.validate_manifest(release, manifest)
        release, manifest = self.release()
        for field, value in [('size', -1), ('filename', '../evil.exe'), ('version', '9.0.0'), ('sha256', 'bad')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                updater.validate_manifest(release, dict(manifest, **{field: value}))

    def test_download_checks_hash_and_cleans_partial(self):
        release, manifest = self.release()
        update = updater.validate_manifest(release, manifest)
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(updater, 'urlopen', return_value=io.BytesIO(b'abc')):
                self.assertEqual(updater.download(update, folder, lambda *_: None).read_bytes(), b'abc')
            for content in (b'ab', b'bad', b'abcd'):
                with patch.object(updater, 'urlopen', return_value=io.BytesIO(content)), self.assertRaises(ValueError):
                    updater.download(update, folder, lambda *_: None)
                self.assertFalse(list(Path(folder).glob('*.part')))

    def test_cancelled_download_never_completes(self):
        release, manifest = self.release()
        with tempfile.TemporaryDirectory() as folder, patch.object(updater, 'urlopen', return_value=io.BytesIO(b'abc')):
            with self.assertRaises(RuntimeError):
                updater.download(updater.validate_manifest(release, manifest), folder, lambda *_: None, lambda: True)
            self.assertFalse(list(Path(folder).iterdir()))

    def test_no_update_and_prerelease(self):
        release, _ = self.release()
        with patch.object(updater, 'read_json', return_value=release):
            self.assertIsNone(updater.latest('1.4.1'))
            self.assertIsNone(updater.latest('1.5.0'))
            release['prerelease'] = True
            self.assertIsNone(updater.latest('1.0.0'))

    def test_offline_continues_once(self):
        opened = []
        startup = Startup(lambda: opened.append(True), lambda: True)
        with patch('sys.frozen', True, create=True), patch.object(updater, 'latest', side_effect=OSError('offline')), patch('app.desktop.startup.time.sleep'):
            startup.check()
        startup.continue_app()
        self.assertEqual(opened, [True])
        self.assertEqual(startup.state['status'], 'opening')

    def test_splash_api_does_not_expose_internal_objects(self):
        api = SplashAPI(Startup(lambda: None, lambda: True))
        self.assertEqual({name for name in dir(api) if not name.startswith('_')},
                         {'get_state', 'continue_app', 'install_update'})

    def test_skip_prevents_late_update_prompt(self):
        startup = Startup(lambda: None, lambda: True)
        startup.continue_app()
        with patch('sys.frozen', True, create=True), patch.object(updater, 'latest', return_value={'version':'1.4.1'}):
            startup.check()
        self.assertIsNone(startup.update)

    def test_install_not_exposed_after_splash(self):
        startup = Startup(lambda: None, lambda: True)
        startup.state['status'] = 'available'
        startup.update = {'version':'1.4.1'}
        startup.continue_app()
        with patch('app.desktop.startup.threading.Thread') as thread:
            startup.install_update()
            thread.assert_not_called()

    def test_powershell_literal_quotes(self):
        self.assertEqual(updater.ps_literal("C:/O'Brien/$test.exe"), "'C:/O''Brien/$test.exe'")

    def test_installer_helper_environment_and_dll_restore(self):
        for launch_error in (None, OSError("helper unavailable")):
            with self.subTest(error=launch_error), tempfile.TemporaryDirectory() as folder:
                installer = Path(folder) / "setup.exe"
                installer.write_bytes(b"verified")
                update = dict(version="1.4.4", sha256=hashlib.sha256(b"verified").hexdigest())
                kernel = MagicMock()
                with patch('sys.frozen', True, create=True), patch('sys.executable', str(Path(folder) / 'app.exe')), \
                     patch.dict(updater.os.environ, {"WINDIR": "C:/Windows"}), \
                     patch.object(updater.ctypes, 'WinDLL', return_value=kernel, create=True), \
                     patch.object(updater.subprocess, 'CREATE_NO_WINDOW', 0, create=True), \
                     patch.object(updater.subprocess, 'Popen', side_effect=launch_error) as launch:
                    if launch_error:
                        with self.assertRaises(OSError):
                            updater.launch_installer(installer, update)
                    else:
                        updater.launch_installer(installer, update)
                    self.assertEqual(kernel.SetDllDirectoryW.call_count, 2)
                    options = launch.call_args.kwargs
                    self.assertEqual(options['env']['PYINSTALLER_RESET_ENVIRONMENT'], '1')
                    self.assertTrue(options['env']['PSModulePath'].endswith('Modules'))
                    self.assertEqual(options['cwd'], str(Path(folder).resolve()))
                    script = (Path(folder) / 'install-update.ps1').read_text(encoding='utf-8-sig')
                    self.assertIn('SHA256]::Create()', script)
                    self.assertNotIn('Get-FileHash', script)
