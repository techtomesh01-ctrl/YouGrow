package com.yougrow.app

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * Native YouGrow starter UI.
 *
 * This screen is built from Android views (not a WebView). Shared sign-in,
 * live creator listings, moderation and points require the backend API to be
 * deployed and connected before production use.
 */
class MainActivity : Activity() {
    private val bg = Color.rgb(12, 15, 24)
    private val panel = Color.rgb(24, 29, 43)
    private val accent = Color.rgb(103, 232, 166)
    private val muted = Color.rgb(167, 177, 196)
    private lateinit var root: LinearLayout
    private lateinit var content: LinearLayout
    private lateinit var search: EditText
    private var currentTab = "Home"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        window.decorView.systemUiVisibility = 0
        buildShell()
        showHome()
    }

    private fun buildShell() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(bg)
            setPadding(dp(18), dp(12), dp(18), dp(8))
        }
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val brand = TextView(this).apply {
            text = "YouGrow"
            textSize = 27f
            setTextColor(Color.WHITE)
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
        }
        val spacer = View(this)
        val badge = TextView(this).apply {
            text = "CREATOR COMMUNITY"
            textSize = 10f
            setTextColor(accent)
            setPadding(dp(10), dp(7), dp(10), dp(7))
            background = rounded(Color.rgb(24, 53, 47), 18)
        }
        header.addView(brand)
        header.addView(spacer, LinearLayout.LayoutParams(0, 1, 1f))
        header.addView(badge)
        root.addView(header)

        val subtitle = TextView(this).apply {
            text = "Discover creators. Grow together."
            textSize = 14f
            setTextColor(muted)
            setPadding(0, dp(4), 0, dp(14))
        }
        root.addView(subtitle)

        search = EditText(this).apply {
            hint = "Search creators or categories"
            setHintTextColor(muted)
            setTextColor(Color.WHITE)
            textSize = 15f
            setSingleLine(true)
            setPadding(dp(14), dp(4), dp(14), dp(4))
            background = rounded(panel, 14)
        }
        root.addView(search, LinearLayout.LayoutParams(-1, dp(50)).apply { bottomMargin = dp(12) })
        search.setOnEditorActionListener { _, _, _ ->
            currentTab = "Discover"
            showDiscover(search.text.toString())
            true
        }

        val scroll = ScrollView(this).apply { clipToPadding = false }
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 0, 0, dp(12))
        }
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))

        val nav = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(0, dp(8), 0, dp(2))
        }
        listOf("Home", "Discover", "Tasks", "Profile").forEach { tab ->
            val button = TextView(this).apply {
                text = tab
                textSize = 12f
                gravity = Gravity.CENTER
                setTextColor(if (tab == currentTab) accent else muted)
                setPadding(dp(7), dp(12), dp(7), dp(12))
                setOnClickListener { selectTab(tab) }
            }
            nav.addView(button, LinearLayout.LayoutParams(0, dp(46), 1f))
        }
        root.addView(nav)
        setContentView(root)
    }

    private fun selectTab(tab: String) {
        currentTab = tab
        when (tab) {
            "Home" -> showHome()
            "Discover" -> showDiscover(search.text.toString())
            "Tasks" -> showTasks()
            else -> showProfile()
        }
        // Refresh the tab highlight by rebuilding the shell would reset scroll,
        // so the selected page heading provides the current navigation context.
    }

    private fun showHome() {
        content.removeAllViews()
        content.addView(heroCard())
        heading("Explore the community")
        body("Find channels by interest, then decide for yourself which creators you want to watch or follow.")
        heading("Quick access")
        actionCard("Discover creators", "Browse channels by category", "Explore") { selectTab("Discover") }
        actionCard("Community tasks", "Learn about permitted in-app activities", "View tasks") { selectTab("Tasks") }
        actionCard("Your profile", "Account and app status", "Open profile") { selectTab("Profile") }
        note("Starter app: shared accounts and live data will appear after the secure backend is connected.")
    }

    private fun heroCard(): View {
        val box = cardContainer()
        val label = TextView(this).apply {
            text = "YOUR NEXT STEP STARTS HERE"
            textSize = 11f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(accent)
        }
        box.addView(label)
        val title = TextView(this).apply {
            text = "Create. Discover. Grow."
            textSize = 25f
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
            setTextColor(Color.WHITE)
            setPadding(0, dp(10), 0, dp(8))
        }
        box.addView(title)
        val desc = TextView(this).apply {
            text = "A community for discovering creators and building your own presence."
            textSize = 14f
            setTextColor(muted)
        }
        box.addView(desc)
        val btn = makeButton("Explore creators")
        btn.setOnClickListener { selectTab("Discover") }
        box.addView(btn, LinearLayout.LayoutParams(-1, dp(48)).apply { topMargin = dp(18) })
        return box
    }

    private fun showDiscover(query: String = "") {
        content.removeAllViews()
        heading("Discover creators")
        body("Search opens YouTube so you can explore channels directly. These are discovery links, not verified or live member listings.")
        val q = query.trim()
        actionCard("YouTube search", if (q.isBlank()) "Find creators on YouTube" else "Search YouTube for: $q", "Open") {
            val term = if (q.isBlank()) "YouTube creators" else q
            openUrl("https://www.youtube.com/results?search_query=" + Uri.encode(term))
        }
        listOf(
            "Education" to "Discover learning and tutorial channels",
            "Technology" to "Explore gadgets, coding and tech news",
            "Gaming" to "Find gaming creators and gameplay",
            "Entertainment" to "Explore music, comedy and entertainment",
            "Business" to "Learn about business and entrepreneurship"
        ).forEach { (name, description) ->
            actionCard(name, description, "Search") {
                openUrl("https://www.youtube.com/results?search_query=" + Uri.encode(name + " creators"))
            }
        }
        note("YouGrow does not give rewards for YouTube subscriptions, views, likes, comments or shares.")
    }

    private fun showTasks() {
        content.removeAllViews()
        heading("Community tasks")
        body("This page explains the rules. No points are being issued in this starter build because the secure account and points backend is not connected yet.")
        actionCard("Profile setup", "Complete your profile when account services are enabled", "Details") {
            showMessage("Profile setup will be available after account services are connected.")
        }
        actionCard("Community safety", "Report misleading or inappropriate creator listings", "Guidelines") {
            showMessage("Please use YouTube's own reporting tools for content hosted on YouTube.")
        }
        note("Important: no cash, points or prizes are offered in exchange for YouTube engagement. Any future rewards must be for permitted in-app activities only.")
    }

    private fun showProfile() {
        content.removeAllViews()
        heading("Your profile")
        body("Account sign-in is not connected in this native starter build.")
        actionCard("Account status", "Shared registration and secure login need the backend API", "Status") {
            showMessage("No account has been created from this screen. Backend connection is still required.")
        }
        actionCard("Language", "YouGrow is designed for Hindi and English users", "Language") {
            showMessage("Hindi and English language switching is planned; it is not active in this starter build.")
        }
        actionCard("Help & safety", "Use the app responsibly and respect platform rules", "Read") {
            showMessage("Never share your password or verification codes with anyone.")
        }
    }

    private fun heading(text: String) {
        content.addView(TextView(this).apply {
            this.text = text
            textSize = 20f
            typeface = Typeface.create("sans-serif", Typeface.BOLD)
            setTextColor(Color.WHITE)
            setPadding(0, dp(18), 0, dp(8))
        })
    }

    private fun body(text: String) {
        content.addView(TextView(this).apply {
            this.text = text
            textSize = 14f
            setTextColor(muted)
            setLineSpacing(dp(3).toFloat(), 1f)
            setPadding(0, 0, 0, dp(12))
        })
    }

    private fun note(text: String) {
        val v = TextView(this).apply {
            this.text = text
            textSize = 12f
            setTextColor(muted)
            setPadding(dp(12), dp(12), dp(12), dp(12))
            background = rounded(Color.rgb(30, 35, 48), 12)
        }
        content.addView(v, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(14) })
    }

    private fun actionCard(title: String, description: String, buttonLabel: String, action: () -> Unit) {
        val box = cardContainer()
        val titleView = TextView(this).apply {
            text = title
            textSize = 17f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
        }
        box.addView(titleView)
        val desc = TextView(this).apply {
            text = description
            textSize = 13f
            setTextColor(muted)
            setPadding(0, dp(5), 0, dp(12))
        }
        box.addView(desc)
        val btn = makeButton(buttonLabel)
        btn.setOnClickListener { action() }
        box.addView(btn, LinearLayout.LayoutParams(-1, dp(42)))
        content.addView(box, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
    }

    private fun cardContainer(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(16), dp(16), dp(16))
        background = rounded(panel, 18)
    }

    private fun makeButton(label: String): Button = Button(this).apply {
        text = label
        textSize = 14f
        isAllCaps = false
        setTextColor(Color.rgb(8, 25, 19))
        background = rounded(accent, 12)
        stateListAnimator = null
    }

    private fun rounded(color: Int, radius: Int): GradientDrawable =
        GradientDrawable().apply { setColor(color); cornerRadius = dp(radius).toFloat() }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun openUrl(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (_: Exception) {
            showMessage("Could not open the link on this device.")
        }
    }

    private fun showMessage(message: String) {
        android.widget.Toast.makeText(this, message, android.widget.Toast.LENGTH_LONG).show()
    }
}
