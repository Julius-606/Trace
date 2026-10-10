package com.example.edu_ai.schemas

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    @SerializedName("email") val email: String,
    @SerializedName("password") val password: String
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("role") val role: String
)

data class SendOtpRequest(
    @SerializedName("email") val email: String,
    @SerializedName("action") val action: String = "signup" // "signup" or "forgot_password"
)

data class SendOtpResponse(
    @SerializedName("status") val status: String,
    @SerializedName("message") val message: String,
    @SerializedName("email") val email: String,
    @SerializedName("otp_preview") val otpPreview: String? = null
)

data class VerifyOtpRequest(
    @SerializedName("email") val email: String,
    @SerializedName("otp") val otp: String,
    @SerializedName("action") val action: String = "signup"
)

data class ForgotPasswordResetRequest(
    @SerializedName("email") val email: String,
    @SerializedName("otp") val otp: String,
    @SerializedName("new_password") val newPassword: String
)

data class GenericAuthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("message") val message: String
)

data class SignupRequest(
    @SerializedName("full_name") val fullName: String,
    @SerializedName("email") val email: String,
    @SerializedName("password") val password: String,
    @SerializedName("otp") val otp: String,
    @SerializedName("age") val age: Int? = null,
    @SerializedName("level_of_study") val levelOfStudy: String? = null,
    @SerializedName("course_pursued") val coursePursued: String? = null,
    @SerializedName("referral_code") val referralCode: String? = null,
    @SerializedName("username") val username: String? = null,
    @SerializedName("role") val role: String = "Student"
)
