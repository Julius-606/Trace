
package com.example.edu_ai.data.remote.ai

import android.util.Log
import com.example.edu_ai.BuildConfig

/**
 * 🔑 The Key Rotary System
 */
object GeminiKeyManager {
    
    private val apiKeys: List<String> = listOfNotNull(
        BuildConfig.GEMINI_API_KEY.takeIf { it.isNotBlank() },
        BuildConfig.GEMINI_API_KEY_1.takeIf { it.isNotBlank() },
        BuildConfig.GEMINI_API_KEY_2.takeIf { it.isNotBlank() }
    )

    private var currentKeyIndex = 0

    /**
     * Returns the current API key in the rotation.
     */
    fun getCurrentKey(): String {
        if (apiKeys.isEmpty()) return ""
        return apiKeys[currentKeyIndex % apiKeys.size]
    }

    /**
     * Swaps to the next key. Returns the new key.
     */
    fun rotateKey(): String {
        if (apiKeys.size <= 1) return getCurrentKey()
        currentKeyIndex = (currentKeyIndex + 1) % apiKeys.size
        Log.d("GeminiKeyManager", "🔄 Swapped to Key Index: $currentKeyIndex")
        return getCurrentKey()
    }

    fun getKeyCount(): Int = apiKeys.size

    /**
     * For debugging, returns the last 4 digits of the current key.
     */
    fun getKeySnippet(): String {
        val key = getCurrentKey()
        return if (key.length > 4) "...${key.takeLast(4)}" else if (key.isNotEmpty()) key else "NOT_CONFIGURED"
    }
    
    // Legacy support for older code
    fun getNextKey(): String = rotateKey()
}


 