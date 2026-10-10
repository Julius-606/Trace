
// IDENTITY: data/remote/EduAIApi.kt
package com.example.edu_ai.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface EduAIApi {

    @GET("api/users/{user_id}/dashboard")
    suspend fun getDashboard(@Path("user_id") userId: String): DashboardResponse

    // --- AI Endpoints ---

    @POST("api/ai/chat")
    suspend fun aiChat(@Body request: ChatRequest): ChatResponse

    @POST("api/ai/quiz")
    suspend fun generateAiQuiz(
        @Body request: QuizRequest,
        @Query("topic") topic: String? = null,
        @Query("subtopic") subtopic: String? = null
    ): ApiQuizResponse

    @POST("api/quiz/record")
    suspend fun recordQuiz(@Body request: QuizRecordRequest): Map<String, String>

    @GET("api/ai/recommendations/{user_id}")
    suspend fun getRecommendations(@Path("user_id") userId: String): RecommendationResponse

    @POST("api/ai/recommendations/{user_id}")
    suspend fun getRecommendationsWithContext(
        @Path("user_id") userId: String,
        @Body payload: ApiStudyContextPayload
    ): RecommendationResponse

    @GET("api/users/{user_id}/timetable")
    suspend fun getTimetable(@Path("user_id") userId: String): ApiTimetableResponse

    @POST("api/users/{user_id}/timetable")
    suspend fun getTimetableWithContext(
        @Path("user_id") userId: String,
        @Body payload: ApiStudyContextPayload
    ): ApiTimetableResponse

    @POST("api/auth/login")
    suspend fun login(@Body request: com.example.edu_ai.schemas.LoginRequest): com.example.edu_ai.schemas.TokenResponse

    @POST("api/auth/send-otp")
    suspend fun sendOtp(@Body request: com.example.edu_ai.schemas.SendOtpRequest): com.example.edu_ai.schemas.SendOtpResponse

    @POST("api/auth/verify-otp")
    suspend fun verifyOtp(@Body request: com.example.edu_ai.schemas.VerifyOtpRequest): com.example.edu_ai.schemas.GenericAuthResponse

    @POST("api/auth/signup")
    suspend fun signup(@Body request: com.example.edu_ai.schemas.SignupRequest): com.example.edu_ai.schemas.TokenResponse

    @POST("api/auth/forgot-password/reset")
    suspend fun resetPassword(@Body request: com.example.edu_ai.schemas.ForgotPasswordResetRequest): com.example.edu_ai.schemas.GenericAuthResponse

    // --- Teacher Endpoints ---

    @GET("api/teacher/dashboard")
    suspend fun getTeacherDashboard(): TeacherDashboardResponse

    @POST("api/teacher/class-report")
    suspend fun generateClassReport(): ClassReportResponse

    @PUT("api/users/{user_id}")
    suspend fun updateStudentProfile(
        @Path("user_id") userId: String,
        @Body updates: Map<String, Any?>
    ): Map<String, Any?>

    @POST("api/teacher/send-report/{student_id}")
    suspend fun sendProgressReport(@Path("student_id") studentId: String): Map<String, Any?>

    // --- Parent Endpoints ---

    @GET("api/parent/dashboard/{student_id}")
    suspend fun getParentDashboard(@Path("student_id") studentId: String): ParentDashboardResponse

    // --- Ingestion / Library Endpoints ---

    @GET("api/units/library")
    suspend fun getLibraryUnits(): List<LibraryUnit>

    @POST("api/units/library/add/{unit_id}")
    suspend fun addUnitToUser(
        @Path("unit_id") unitId: Int,
        @Query("user_id") userId: String
    ): Map<String, String>

    // --- Synchronization & Bookmarking Endpoints ---

    @GET("api/user/{user_id}/sync")
    suspend fun getSyncData(@Path("user_id") userId: String): ApiSyncResponse

    @POST("api/user/{user_id}/sync")
    suspend fun sendSyncData(
        @Path("user_id") userId: String,
        @Body request: ApiSyncRequest
    ): Map<String, Any?>

    @POST("api/user/{user_id}/bookmarks")
    suspend fun saveBookmark(
        @Path("user_id") userId: String,
        @Body bookmark: ApiBookmarkItem
    ): Map<String, Any?>

    // --- System Releases & Mandatory Upgrade Endpoints ---

    @GET("api/system/releases")
    suspend fun getSystemReleases(
        @Query("client_version_code") clientVersionCode: Int
    ): ApiReleasesResponse

    @POST("admin/releases")
    suspend fun createRelease(
        @Body request: CreateReleaseRequest
    ): Map<String, Any?>

    @POST("admin/releases/{release_id}/toggle-mandatory")
    suspend fun toggleMandatoryRelease(
        @Path("release_id") releaseId: Long,
        @Body body: Map<String, Boolean> = emptyMap()
    ): Map<String, Any?>
}


 