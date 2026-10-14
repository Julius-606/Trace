
package com.example.edu_ai.utils

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

object PreferenceManager {
    private const val PREF_NAME = "edu_ai_secure_prefs"
    private const val KEY_AUTH_TOKEN = "auth_token"
    private const val KEY_DEVELOPER_MODE = "developer_mode"
    private const val KEY_ACTIVE_USER_ID = "active_user_id"

    private fun getSharedPrefs(context: Context) = EncryptedSharedPreferences.create(
        context,
        PREF_NAME,
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveToken(context: Context, token: String) {
        getSharedPrefs(context).edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getToken(context: Context): String? {
        return getSharedPrefs(context).getString(KEY_AUTH_TOKEN, null)
    }

    fun clearToken(context: Context) {
        getSharedPrefs(context).edit().remove(KEY_AUTH_TOKEN).apply()
    }

    fun saveActiveUserId(context: Context, userId: String) {
        getSharedPrefs(context).edit().putString(KEY_ACTIVE_USER_ID, userId).apply()
    }

    fun getActiveUserId(context: Context): String? {
        return getSharedPrefs(context).getString(KEY_ACTIVE_USER_ID, null)
    }

    fun clearActiveUserId(context: Context) {
        getSharedPrefs(context).edit().remove(KEY_ACTIVE_USER_ID).apply()
    }

    fun saveDeveloperMode(context: Context, enabled: Boolean) {
        getSharedPrefs(context).edit().putBoolean(KEY_DEVELOPER_MODE, enabled).apply()
    }

    fun isDeveloperMode(context: Context): Boolean {
        return getSharedPrefs(context).getBoolean(KEY_DEVELOPER_MODE, false)
    }

    fun saveBackendMode(context: Context, mode: String) {
        getSharedPrefs(context).edit().putString("backend_mode", mode).apply()
    }

    fun getBackendMode(context: Context): String {
        return getSharedPrefs(context).getString("backend_mode", "cloud") ?: "cloud"
    }

    // --- APPEARANCE & THEMES ---
    fun saveAppTheme(context: Context, theme: String) {
        getSharedPrefs(context).edit().putString("app_theme", theme).apply()
    }

    fun getAppTheme(context: Context): String {
        return getSharedPrefs(context).getString("app_theme", "dark") ?: "dark"
    }

    fun saveThemeAccent(context: Context, accent: String) {
        getSharedPrefs(context).edit().putString("theme_accent", accent).apply()
    }

    fun getThemeAccent(context: Context): String {
        return getSharedPrefs(context).getString("theme_accent", "indigo") ?: "indigo"
    }

    fun saveAppFont(context: Context, font: String) {
        getSharedPrefs(context).edit().putString("app_font", font).apply()
    }

    fun getAppFont(context: Context): String {
        return getSharedPrefs(context).getString("app_font", "sans") ?: "sans"
    }

    // --- ACCOUNT & PROFILE SETTINGS ---
    fun saveUserProfile(context: Context, name: String, email: String, academicLevel: String, persona: String, difficulty: String) {
        getSharedPrefs(context).edit()
            .putString("profile_name", name)
            .putString("profile_email", email)
            .putString("profile_academic_level", academicLevel)
            .putString("profile_persona", persona)
            .putString("profile_difficulty", difficulty)
            .apply()
    }

    fun getUserDisplayName(context: Context): String {
        return getSharedPrefs(context).getString("profile_name", "Medical Scholar") ?: "Medical Scholar"
    }

    fun getUserEmail(context: Context): String {
        return getSharedPrefs(context).getString("profile_email", "student@trace.edu") ?: "student@trace.edu"
    }

    fun getAcademicLevel(context: Context): String {
        return getSharedPrefs(context).getString("profile_academic_level", "Year 3 - Core Clerkships") ?: "Year 3 - Core Clerkships"
    }

    fun getAiPersona(context: Context): String {
        return getSharedPrefs(context).getString("profile_persona", "Socratic Tutor") ?: "Socratic Tutor"
    }

    fun getDifficulty(context: Context): String {
        return getSharedPrefs(context).getString("profile_difficulty", "Standard") ?: "Standard"
    }

    fun getZenithRecommendation(context: Context, userId: String): Pair<String, Long>? {
        val prefs = context.getSharedPreferences("edu_ai_zenith_prefs", Context.MODE_PRIVATE)
        val text = prefs.getString("zenith_rec_$userId", null) ?: return null
        val time = prefs.getLong("zenith_time_$userId", 0L)
        return Pair(text, time)
    }

    fun saveZenithRecommendation(context: Context, userId: String, text: String, timestamp: Long = System.currentTimeMillis()) {
        val prefs = context.getSharedPreferences("edu_ai_zenith_prefs", Context.MODE_PRIVATE)
        prefs.edit()
            .putString("zenith_rec_$userId", text)
            .putLong("zenith_time_$userId", timestamp)
            .apply()
    }

    // --- SUBTOPIC INTERACTION SAVING ---
    fun getSubtopicInquiries(context: Context, subtopicId: Long): String? {
        val prefs = context.getSharedPreferences("edu_ai_inquiries_prefs", Context.MODE_PRIVATE)
        return prefs.getString("inquiries_$subtopicId", null)
    }

    fun saveSubtopicInquiries(context: Context, subtopicId: Long, json: String) {
        val prefs = context.getSharedPreferences("edu_ai_inquiries_prefs", Context.MODE_PRIVATE)
        prefs.edit().putString("inquiries_$subtopicId", json).apply()
    }

    // --- SUBTOPIC EXPLANATION REDO & VERSIONING ---
    fun getSubtopicExplanationVersions(context: Context, subtopicId: Long, stepIndex: Int): List<ExplanationVersion> {
        val prefs = context.getSharedPreferences("edu_ai_explanations_history", Context.MODE_PRIVATE)
        val json = prefs.getString("versions_${subtopicId}_$stepIndex", null) ?: return emptyList()
        return try {
            val listType = object : com.google.gson.reflect.TypeToken<List<ExplanationVersion>>() {}.type
            com.google.gson.Gson().fromJson<List<ExplanationVersion>>(json, listType) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    fun saveSubtopicExplanationVersion(context: Context, subtopicId: Long, stepIndex: Int, version: ExplanationVersion): List<ExplanationVersion> {
        val existing = getSubtopicExplanationVersions(context, subtopicId, stepIndex).toMutableList()
        val dupIdx = existing.indexOfFirst { it.content.trim() == version.content.trim() }
        if (dupIdx >= 0) {
            return existing
        }
        existing.add(version)
        val prefs = context.getSharedPreferences("edu_ai_explanations_history", Context.MODE_PRIVATE)
        prefs.edit().putString("versions_${subtopicId}_$stepIndex", com.google.gson.Gson().toJson(existing)).apply()
        return existing
    }
}

data class ExplanationVersion(
    val id: String = java.util.UUID.randomUUID().toString(),
    val versionNumber: Int = 1,
    val timestamp: Long = System.currentTimeMillis(),
    val content: String = "",
    val tag: String = "Standard"
)


 