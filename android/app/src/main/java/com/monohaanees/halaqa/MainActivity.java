package com.monohaanees.halaqa;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private WebView wv;
    private ValueCallback<Uri[]> fileCb;
    private static final int FILE_REQ = 1;
    private static final int PERM_REQ = 2;
    private String pendName, pendB64;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        wv = new WebView(this);
        setContentView(wv);
        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setTextZoom(100);
        wv.addJavascriptInterface(new Bridge(), "AndroidBridge");
        wv.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("file://")) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception e) { }
                return true;
            }
        });
        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                fileCb = cb;
                try {
                    Intent i = params.createIntent();
                    startActivityForResult(Intent.createChooser(i, "اختر ملف النسخة الاحتياطية"), FILE_REQ);
                } catch (Exception e) {
                    fileCb.onReceiveValue(null);
                    fileCb = null;
                    return false;
                }
                return true;
            }
        });
        wv.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req == FILE_REQ && fileCb != null) {
            fileCb.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res, data));
            fileCb = null;
        } else {
            super.onActivityResult(req, res, data);
        }
    }

    @Override
    public void onRequestPermissionsResult(int req, String[] perms, int[] res) {
        super.onRequestPermissionsResult(req, perms, res);
        if (req == PERM_REQ) {
            if (res.length > 0 && res[0] == 0 && pendName != null) saveLegacy(pendName, pendB64);
            else toast("تعذّر التنزيل: لم تُمنح صلاحية التخزين");
            pendName = null; pendB64 = null;
        }
    }

    private void toast(String m) {
        runOnUiThread(() -> Toast.makeText(this, m, Toast.LENGTH_LONG).show());
    }

    private void saveNow(String name, String b64) {
        if (Build.VERSION.SDK_INT >= 29) {
            try {
                byte[] data = Base64.decode(b64, Base64.DEFAULT);
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, name);
                v.put(MediaStore.Downloads.MIME_TYPE, "text/plain");
                Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                if (uri == null) throw new Exception();
                OutputStream os = getContentResolver().openOutputStream(uri);
                os.write(data); os.close();
                toast("نُزّل الملف إلى مجلد التنزيلات: " + name);
            } catch (Exception e) { toast("تعذّر التنزيل"); }
        } else {
            if (checkSelfPermission("android.permission.WRITE_EXTERNAL_STORAGE") == 0) {
                saveLegacy(name, b64);
            } else {
                pendName = name; pendB64 = b64;
                requestPermissions(new String[]{"android.permission.WRITE_EXTERNAL_STORAGE"}, PERM_REQ);
            }
        }
    }

    private void saveLegacy(String name, String b64) {
        try {
            byte[] data = Base64.decode(b64, Base64.DEFAULT);
            File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            if (!dir.exists()) dir.mkdirs();
            File f = new File(dir, name);
            FileOutputStream fo = new FileOutputStream(f);
            fo.write(data); fo.close();
            toast("نُزّل الملف إلى مجلد التنزيلات: " + name);
        } catch (Exception e) { toast("تعذّر التنزيل"); }
    }

    private void shareNow(String name, String b64) {
        try {
            byte[] data = Base64.decode(b64, Base64.DEFAULT);
            File f = new File(getCacheDir(), name);
            FileOutputStream fo = new FileOutputStream(f);
            fo.write(data); fo.close();
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType("text/plain");
            i.putExtra(Intent.EXTRA_STREAM, FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", f));
            i.putExtra(Intent.EXTRA_SUBJECT, "نسخة احتياطية — سجل الحلقة");
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(i, "مشاركة النسخة عبر"));
        } catch (Exception e) { toast("تعذّرت المشاركة"); }
    }

    class Bridge {
        @JavascriptInterface
        public void save(String name, String b64) { saveNow(name, b64); }

        @JavascriptInterface
        public void share(String name, String b64) { shareNow(name, b64); }
    }
}
