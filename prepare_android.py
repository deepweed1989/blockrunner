"""Patches the generated Capacitor Android project: landscape, fullscreen, launcher icons."""
import os, re, json
from PIL import Image

cfg = json.load(open('capacitor.config.json'))
pkg = cfg['appId']
APP = 'android/app/src/main'
RES = APP + '/res'

# 1) Lock to landscape
mp = APP + '/AndroidManifest.xml'
s = open(mp, encoding='utf-8').read()
if 'screenOrientation' not in s:
    s, n = re.subn(r'(android:name="[^"]*MainActivity")', r'\1\n            android:screenOrientation="sensorLandscape"', s, count=1)
    assert n == 1, 'MainActivity not found in AndroidManifest.xml'
open(mp, 'w', encoding='utf-8').write(s)

# 2) Fullscreen theme, draw into the notch area
sp = RES + '/values/styles.xml'
s = open(sp, encoding='utf-8').read()
if 'windowFullscreen' not in s:
    extra = ('\n        <item name="android:windowFullscreen">true</item>'
             '\n        <item name="android:windowLayoutInDisplayCutoutMode">shortEdges</item>')
    s, n = re.subn(r'(<style name="AppTheme\.NoActionBar"[^>]*>)', lambda m: m.group(1) + extra, s, count=1)
    assert n == 1, 'AppTheme.NoActionBar not found in styles.xml'
open(sp, 'w', encoding='utf-8').write(s)

# 3) Hide the navigation bar too (immersive mode)
jdir = APP + '/java/' + pkg.replace('.', '/')
os.makedirs(jdir, exist_ok=True)
open(jdir + '/MainActivity.java', 'w', encoding='utf-8').write('''package %s;

import android.os.Bundle;
import android.view.View;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        hideBars();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }

    private void hideBars() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }
}
''' % pkg)

# 4) Launcher icons
open(RES + '/values/ic_launcher_background.xml', 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#34363D</color>\n</resources>\n')
legacy = Image.open('icon-512.png').convert('RGBA')
adaptive = Image.open('icon-maskable-512.png').convert('RGBA')
for d, (small, big) in {'mdpi': (48, 108), 'hdpi': (72, 162), 'xhdpi': (96, 216), 'xxhdpi': (144, 324), 'xxxhdpi': (192, 432)}.items():
    folder = '%s/mipmap-%s' % (RES, d)
    os.makedirs(folder, exist_ok=True)
    legacy.resize((small, small), Image.LANCZOS).save(folder + '/ic_launcher.png')
    legacy.resize((small, small), Image.LANCZOS).save(folder + '/ic_launcher_round.png')
    adaptive.resize((big, big), Image.LANCZOS).save(folder + '/ic_launcher_foreground.png')
print('Android project patched OK')
