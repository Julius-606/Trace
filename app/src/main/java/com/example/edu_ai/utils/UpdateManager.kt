package com.example.edu_ai.utils

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import com.example.edu_ai.data.remote.ApiAppRelease
import com.example.edu_ai.data.remote.RetrofitClient
import com.example.edu_ai.repository.EduAIRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

object UpdateManager {
    const val CURRENT_VERSION_NAME = "1.0.0"
    const val CURRENT_VERSION_CODE = 1

    private val _isChecking = MutableStateFlow(false)
    val isChecking: StateFlow<Boolean> = _isChecking.asStateFlow()

    private val _mandatoryUpdateRequired = MutableStateFlow(false)
    val mandatoryUpdateRequired: StateFlow<Boolean> = _mandatoryUpdateRequired.asStateFlow()

    private val _mandatoryRelease = MutableStateFlow<ApiAppRelease?>(null)
    val mandatoryRelease: StateFlow<ApiAppRelease?> = _mandatoryRelease.asStateFlow()

    private val _latestRelease = MutableStateFlow<ApiAppRelease?>(null)
    val latestRelease: StateFlow<ApiAppRelease?> = _latestRelease.asStateFlow()

    private val _releases = MutableStateFlow<List<ApiAppRelease>>(emptyList())
    val releases: StateFlow<List<ApiAppRelease>> = _releases.asStateFlow()

    private val _lastCheckedTime = MutableStateFlow(0L)
    val lastCheckedTime: StateFlow<Long> = _lastCheckedTime.asStateFlow()

    private var pollingJob: Job? = null

    fun startPeriodicCheck(scope: CoroutineScope, repository: EduAIRepository) {
        pollingJob?.cancel()
        pollingJob = scope.launch(Dispatchers.IO) {
            while (isActive) {
                checkForUpdates(repository)
                delay(30_000) // Poll admin archives every 30 seconds for triggers
            }
        }
    }

    suspend fun checkForUpdates(repository: EduAIRepository, onComplete: ((Boolean) -> Unit)? = null) {
        _isChecking.value = true
        try {
            val response = repository.getSystemReleases(clientVersionCode = CURRENT_VERSION_CODE)
            val releaseList = response.releases
            _releases.value = releaseList
            _lastCheckedTime.value = System.currentTimeMillis()

            val latest = releaseList.firstOrNull()
            _latestRelease.value = latest

            // Determine if mandatory update is enforced
            val mandatory = releaseList.firstOrNull { it.isMandatory }
            val isMandatoryActive = response.mandatoryUpdateActive || (mandatory != null && mandatory.versionCode > CURRENT_VERSION_CODE)

            _mandatoryRelease.value = mandatory
            _mandatoryUpdateRequired.value = isMandatoryActive
            onComplete?.invoke(true)
        } catch (e: Exception) {
            e.printStackTrace()
            onComplete?.invoke(false)
        } finally {
            _isChecking.value = false
        }
    }

    fun openDownloadUrl(context: Context, url: String) {
        try {
            val resolvedUrl = if (url.startsWith("/")) {
                val base = RetrofitClient.getBaseUrl().trimEnd('/')
                "$base$url"
            } else if (!url.startsWith("http://") && !url.startsWith("https://")) {
                val base = RetrofitClient.getBaseUrl().trimEnd('/')
                "$base/$url"
            } else {
                url
            }
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(resolvedUrl)).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(context, "Opening link: $url", Toast.LENGTH_SHORT).show()
        }
    }
}
