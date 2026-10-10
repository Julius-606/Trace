
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.google.devtools.ksp)
}

android {
    namespace = "com.example.edu_ai"
    compileSdk = 35

    val backendBaseUrl = (project.findProperty("backendBaseUrl") as? String)
        ?: "https://agent606-trace.hf.space/"
    val fallbackBackendBaseUrl = (project.findProperty("fallbackBackendBaseUrl") as? String)
        ?: "https://untropic-rozanne-noncomprehendingly.ngrok-free.dev/"

    val internalApiKey = (project.findProperty("INTERNAL_API_KEY") as? String) ?: "64923e4d8f1a2c5b9e0f3d7a6c5b9eX0f3d7a6c5b9e0f3d7a"

    val geminiApiKey = (project.findProperty("GEMINI_API_KEY") as? String)
        ?: System.getenv("GEMINI_API_KEY") ?: ""
    val geminiApiKey1 = (project.findProperty("GEMINI_API_KEY_1") as? String)
        ?: System.getenv("GEMINI_API_KEY_1") ?: ""
    val geminiApiKey2 = (project.findProperty("GEMINI_API_KEY_2") as? String)
        ?: System.getenv("GEMINI_API_KEY_2") ?: ""

    defaultConfig {
        applicationId = "com.aistudio.trace.eduxy"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        buildConfigField("String", "BACKEND_BASE_URL", "\"$backendBaseUrl\"")
        buildConfigField("String", "FALLBACK_BACKEND_BASE_URL", "\"$fallbackBackendBaseUrl\"")
        buildConfigField("String", "INTERNAL_API_KEY", "\"$internalApiKey\"")
        buildConfigField("String", "GEMINI_API_KEY", "\"$geminiApiKey\"")
        buildConfigField("String", "GEMINI_API_KEY_1", "\"$geminiApiKey1\"")
        buildConfigField("String", "GEMINI_API_KEY_2", "\"$geminiApiKey2\"")

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("debugConfig") {
            storeFile = file("${rootDir}/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debugConfig")
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.animation)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.google.generativeai)
    implementation(libs.androidx.security.crypto)

    // Retrofit
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)

    // Room
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // Coroutines
    implementation(libs.kotlinx.coroutines.android)

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}

tasks.register("unitTestClasses") {
    dependsOn(tasks.matching { it.name.contains("UnitTestSources") })
}


 