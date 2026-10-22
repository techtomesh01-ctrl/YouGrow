package com.yougrow.app

import android.app.Activity
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import android.widget.Toast

class MainActivity : Activity() {
    private lateinit var web: WebView
    // Replace with the actual HTTPS URL after YouGrow is deployed.
    private val baseUrl = "https://SET-YOUR-YOUGROW-URL.onrender.com"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.webViewClient = WebViewClient()
        web.webChromeClient = WebChromeClient()
        setContentView(web)
        if (baseUrl.contains("SET-YOUR-YOUGROW-URL")) {
            Toast.makeText(this, "Deploy YouGrow, then set its HTTPS URL in MainActivity.kt.", Toast.LENGTH_LONG).show()
        }
        web.loadUrl(baseUrl)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
}
