
// IDENTITY: data/remote/RetrofitClient.kt
package com.example.edu_ai.data.remote

import android.content.Context
import android.util.Log
import com.example.edu_ai.BuildConfig
import com.example.edu_ai.utils.PreferenceManager
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

object RetrofitClient {
    private var currentBaseUrl = BuildConfig.BACKEND_BASE_URL
    private const val FALLBACK_URL = BuildConfig.FALLBACK_BACKEND_BASE_URL
    private const val INTERNAL_API_KEY = BuildConfig.INTERNAL_API_KEY

    fun getBaseUrl(): String = currentBaseUrl

    private var context: Context? = null

    fun init(context: Context) {
        this.context = context.applicationContext
    }

    private class FallbackInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val originalRequest = chain.request()
            
            // Resolve custom backend mode
            context?.let { ctx ->
                val mode = PreferenceManager.getBackendMode(ctx)
                if (mode != "cloud") {
                    val customUrl = if (mode == "container") {
                        originalRequest.url.newBuilder()
                            .scheme("http")
                            .host("10.0.2.2") // Loopback to host machine from Emulator
                            .port(8001)
                            .build()
                    } else { // "ngrok"
                        originalRequest.url.newBuilder()
                            .scheme("https")
                            .host("untropic-rozanne-noncomprehendingly.ngrok-free.dev")
                            .port(443)
                            .build()
                    }
                    
                    val customRequest = originalRequest.newBuilder()
                        .url(customUrl)
                        .build()
                    
                    return chain.proceed(customRequest)
                }
            }

            try {
                return chain.proceed(originalRequest)
            } catch (e: IOException) {
                Log.e("RetrofitClient", "Primary backend failed: ${e.message}. Attempting fallback...")
                
                if (currentBaseUrl != FALLBACK_URL) {
                    currentBaseUrl = FALLBACK_URL
                    
                    // Reconstruct request with fallback URL (Hugging Face / Ngrok as fallback)
                    val newUrl = originalRequest.url.newBuilder()
                        .scheme("https")
                        .host("untropic-rozanne-noncomprehendingly.ngrok-free.dev")
                        .port(443)
                        .build()
                    
                    val newRequest = originalRequest.newBuilder()
                        .url(newUrl)
                        .build()
                    
                    return chain.proceed(newRequest)
                }
                throw e
            }
        }
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(FallbackInterceptor())
        .addInterceptor { chain ->
            val requestBuilder = chain.request().newBuilder()
                .addHeader("X-Internal-Api-Key", INTERNAL_API_KEY)
            
            context?.let { ctx ->
                PreferenceManager.getToken(ctx)?.let { token ->
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
            }
            
            chain.proceed(requestBuilder.build())
        }
        .connectTimeout(120, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .writeTimeout(120, TimeUnit.SECONDS)
        .build()

    val instance: EduAIApi by lazy {
        Retrofit.Builder()
            .baseUrl(currentBaseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(EduAIApi::class.java)
    }
}


 