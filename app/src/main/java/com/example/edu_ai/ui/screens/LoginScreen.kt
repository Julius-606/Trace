package com.example.edu_ai.ui.screens

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.edu_ai.BuildConfig
import com.example.edu_ai.EduAIApplication
import com.example.edu_ai.data.local.UserEntity
import com.example.edu_ai.data.remote.RetrofitClient
import com.example.edu_ai.schemas.*
import com.example.edu_ai.utils.PreferenceManager
import com.example.edu_ai.utils.TactileFeedback
import kotlinx.coroutines.launch
import java.security.MessageDigest

private fun hashPassword(password: String): String {
    val bytes = password.toByteArray()
    val md = MessageDigest.getInstance("SHA-256")
    val digest = md.digest(bytes)
    return digest.fold("") { str, it -> str + "%02x".format(it) }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(onLoginSuccess: (String, String) -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    var isSignUpMode by remember { mutableStateOf(false) }
    var backendMode by remember { mutableStateOf(PreferenceManager.getBackendMode(context)) }

    // Sign In Fields
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var isPasswordVisible by remember { mutableStateOf(false) }

    // Create Account Fields
    var signUpFullName by remember { mutableStateOf("") }
    var signUpEmail by remember { mutableStateOf("") }
    var signUpOtp by remember { mutableStateOf("") }
    var signUpPassword by remember { mutableStateOf("") }
    var isSignUpPasswordVisible by remember { mutableStateOf(false) }
    var signUpAge by remember { mutableStateOf("23") }
    var signUpLevelOfStudy by remember { mutableStateOf("Year 4 - Senior Clerkship") }
    var signUpCoursePursued by remember { mutableStateOf("MBChB - Medicine & Surgery") }
    var signUpReferralCode by remember { mutableStateOf("") }
    var isLevelDropdownExpanded by remember { mutableStateOf(false) }

    // OTP Sending State (Signup)
    var isSendingSignUpOtp by remember { mutableStateOf(false) }
    var signUpOtpStatusMessage by remember { mutableStateOf<String?>(null) }
    var isSignUpOtpSentSuccess by remember { mutableStateOf(false) }

    // Forgot Password Modal State
    var showForgotPasswordDialog by remember { mutableStateOf(false) }
    var forgotEmail by remember { mutableStateOf("") }
    var forgotOtp by remember { mutableStateOf("") }
    var forgotNewPassword by remember { mutableStateOf("") }
    var forgotConfirmPassword by remember { mutableStateOf("") }
    var isSendingForgotOtp by remember { mutableStateOf(false) }
    var isResettingPassword by remember { mutableStateOf(false) }
    var forgotOtpStatusMessage by remember { mutableStateOf<String?>(null) }
    var forgotErrorMessage by remember { mutableStateOf<String?>(null) }

    // General Screen State
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var successMessage by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(false) }

    val levelsList = remember {
        listOf(
            "Year 1 - Pre-Clinical",
            "Year 2 - Basic Sciences",
            "Year 3 - Junior Clerkship",
            "Year 4 - Senior Clerkship",
            "Year 5 - Final Year Candidate",
            "Post-Graduate / Resident"
        )
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        MaterialTheme.colorScheme.surface,
                        MaterialTheme.colorScheme.background,
                        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                    )
                )
            )
            .statusBarsPadding()
            .navigationBarsPadding()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(horizontal = 24.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Top
        ) {

            // Header Branding Icon
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = MaterialTheme.colorScheme.primaryContainer,
                modifier = Modifier.size(64.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.Default.School,
                        contentDescription = "Trace Logo",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(36.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            Text(
                text = "Edu-AI Trace",
                fontSize = 28.sp,
                fontWeight = FontWeight.Black,
                color = MaterialTheme.colorScheme.primary,
                letterSpacing = (-0.5).sp
            )
            Text(
                text = if (isSignUpMode) "Enroll in Adaptive Clinical & Academic Vault" else "Sign in to access your workspace",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Navigation Toggle Tabs: [Sign In] vs [Create Account]
            Surface(
                shape = RoundedCornerShape(14.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(4.dp)
                ) {
                    Button(
                        onClick = {
                            TactileFeedback.triggerSubtleClick(context)
                            isSignUpMode = false
                            errorMessage = null
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (!isSignUpMode) MaterialTheme.colorScheme.primary else Color.Transparent,
                            contentColor = if (!isSignUpMode) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                        ),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(42.dp),
                        elevation = ButtonDefaults.buttonElevation(defaultElevation = if (!isSignUpMode) 2.dp else 0.dp)
                    ) {
                        Text("SIGN IN", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }

                    Button(
                        onClick = {
                            TactileFeedback.triggerSubtleClick(context)
                            isSignUpMode = true
                            errorMessage = null
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isSignUpMode) MaterialTheme.colorScheme.primary else Color.Transparent,
                            contentColor = if (isSignUpMode) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                        ),
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier
                            .weight(1f)
                            .height(42.dp),
                        elevation = ButtonDefaults.buttonElevation(defaultElevation = if (isSignUpMode) 2.dp else 0.dp)
                    ) {
                        Text("CREATE ACCOUNT", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Global Error & Success Alerts
            if (errorMessage != null) {
                Surface(
                    color = MaterialTheme.colorScheme.errorContainer,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 14.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.ErrorOutline, contentDescription = null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = errorMessage!!, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onErrorContainer)
                    }
                }
            }

            if (successMessage != null) {
                Surface(
                    color = Color(0xFF10B981).copy(alpha = 0.15f),
                    shape = RoundedCornerShape(12.dp),
                    border = BorderStroke(1.dp, Color(0xFF10B981).copy(alpha = 0.4f)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 14.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = successMessage!!, style = MaterialTheme.typography.bodySmall, color = Color(0xFF10B981), fontWeight = FontWeight.Bold)
                    }
                }
            }

            // =================================================================
            // MODE 1: SIGN IN FORM
            // =================================================================
            if (!isSignUpMode) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                    ),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        // Email Field
                        OutlinedTextField(
                            value = email,
                            onValueChange = { email = it },
                            label = { Text("Email Address or Username") },
                            leadingIcon = {
                                Icon(Icons.Default.Email, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("login_email_input")
                        )

                        // Password Field
                        OutlinedTextField(
                            value = password,
                            onValueChange = { password = it },
                            label = { Text("Password") },
                            leadingIcon = {
                                Icon(Icons.Default.Lock, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            },
                            trailingIcon = {
                                IconButton(onClick = { isPasswordVisible = !isPasswordVisible }) {
                                    Icon(
                                        imageVector = if (isPasswordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                        contentDescription = if (isPasswordVisible) "Hide password" else "Show password"
                                    )
                                }
                            },
                            visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("login_password_input")
                        )

                        // Forgot Password Link Button (Direct User Request)
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.End
                        ) {
                            TextButton(
                                onClick = {
                                    TactileFeedback.triggerSubtleClick(context)
                                    forgotEmail = email.trim()
                                    forgotOtp = ""
                                    forgotNewPassword = ""
                                    forgotConfirmPassword = ""
                                    forgotErrorMessage = null
                                    forgotOtpStatusMessage = null
                                    showForgotPasswordDialog = true
                                },
                                contentPadding = PaddingValues(horizontal = 4.dp, vertical = 2.dp),
                                modifier = Modifier.testTag("forgot_password_button")
                            ) {
                                Text(
                                    text = "Forgot password?",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                        }

                        // Submit Sign In Button
                        Button(
                            onClick = {
                                if (email.isNotBlank() && password.isNotBlank()) {
                                    isLoading = true
                                    errorMessage = null
                                    successMessage = null
                                    scope.launch {
                                        try {
                                            val response = RetrofitClient.instance.login(LoginRequest(email.trim(), password))
                                            PreferenceManager.saveToken(context, response.accessToken)
                                            PreferenceManager.saveActiveUserId(context, response.userId)

                                            // Cache credentials locally in Room database for offline vault login
                                            val app = context.applicationContext as EduAIApplication
                                            val dao = app.database.dao()
                                            val existingUser = dao.getUserById(response.userId)
                                            val passHash = hashPassword(password)
                                            val userEntity = existingUser?.copy(
                                                email = email.trim(),
                                                passwordHash = passHash,
                                                fullName = response.username
                                            ) ?: UserEntity(
                                                id = response.userId,
                                                username = response.username,
                                                role = response.role,
                                                sensoryMode = "Visual",
                                                semesterStatus = "Active",
                                                aiPersona = "Socratic Mentor",
                                                email = email.trim(),
                                                passwordHash = passHash,
                                                fullName = response.username
                                            )
                                            dao.insertUser(userEntity)
                                            TactileFeedback.triggerSuccess(context)
                                            onLoginSuccess(response.role, response.userId)
                                        } catch (e: Exception) {
                                            // Offline login fallback
                                            try {
                                                val app = context.applicationContext as EduAIApplication
                                                val dao = app.database.dao()
                                                val localUser = dao.getUserByEmailOrUsername(email.trim())
                                                val passHash = hashPassword(password)
                                                if (localUser != null && localUser.passwordHash == passHash) {
                                                    PreferenceManager.saveToken(context, "cached_offline_token")
                                                    PreferenceManager.saveActiveUserId(context, localUser.id)
                                                    TactileFeedback.triggerSuccess(context)
                                                    onLoginSuccess(localUser.role, localUser.id)
                                                } else if (localUser != null) {
                                                    errorMessage = "Offline login failed: Incorrect password."
                                                } else {
                                                    errorMessage = "Login failed: Server unreachable and account not cached on device."
                                                }
                                            } catch (dbEx: Exception) {
                                                errorMessage = "Login error: ${e.message}"
                                            }
                                        } finally {
                                            isLoading = false
                                        }
                                    }
                                } else {
                                    errorMessage = "Please enter both your email/username and password."
                                }
                            },
                            enabled = !isLoading,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(50.dp)
                                .testTag("login_submit_button")
                        ) {
                            if (isLoading) {
                                CircularProgressIndicator(modifier = Modifier.size(22.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimary)
                            } else {
                                Text("SIGN IN", fontSize = 15.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Fast-Track Admin Console Button
                OutlinedButton(
                    onClick = {
                        TactileFeedback.triggerSubtleClick(context)
                        PreferenceManager.saveActiveUserId(context, "admin_root")
                        PreferenceManager.saveToken(context, "admin_fast_track_token")
                        onLoginSuccess("Admin", "admin_root")
                    },
                    shape = RoundedCornerShape(14.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(46.dp)
                        .testTag("admin_fast_track_button")
                ) {
                    Icon(Icons.Default.AdminPanelSettings, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("⚡ Fast-Track: Enter Admin Console", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                }
            }

            // =================================================================
            // MODE 2: CREATE ACCOUNT FORM (Direct User Request Specifications)
            // =================================================================
            if (isSignUpMode) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                    ),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        Text(
                            text = "New Student Enrollment",
                            fontWeight = FontWeight.Black,
                            fontSize = 16.sp,
                            color = MaterialTheme.colorScheme.primary
                        )

                        // 1. Full Name
                        OutlinedTextField(
                            value = signUpFullName,
                            onValueChange = { signUpFullName = it },
                            label = { Text("1. Full Name") },
                            placeholder = { Text("e.g. Dr. Julius Kiptoo") },
                            leadingIcon = {
                                Icon(Icons.Default.Person, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            },
                            singleLine = true,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("signup_fullname_input")
                        )

                        // 2. Verified Email with OTP
                        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                OutlinedTextField(
                                    value = signUpEmail,
                                    onValueChange = {
                                        signUpEmail = it
                                        isSignUpOtpSentSuccess = false
                                    },
                                    label = { Text("2. Email Address") },
                                    placeholder = { Text("student@university.edu") },
                                    leadingIcon = {
                                        Icon(Icons.Default.Email, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                                    },
                                    singleLine = true,
                                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                                    shape = RoundedCornerShape(14.dp),
                                    modifier = Modifier
                                        .weight(1f)
                                        .testTag("signup_email_input")
                                )

                                Button(
                                    onClick = {
                                        val clean = signUpEmail.trim()
                                        if (clean.isBlank() || !clean.contains("@")) {
                                            errorMessage = "Please enter a valid email address to receive verification OTP."
                                        } else {
                                            isSendingSignUpOtp = true
                                            errorMessage = null
                                            signUpOtpStatusMessage = "Dispatching OTP code to $clean..."
                                            scope.launch {
                                                try {
                                                    val res = RetrofitClient.instance.sendOtp(
                                                        SendOtpRequest(email = clean, action = "signup")
                                                    )
                                                    isSignUpOtpSentSuccess = true
                                                    signUpOtpStatusMessage = res.message + (res.otpPreview?.let { " [Code: $it]" } ?: "")
                                                    if (!res.otpPreview.isNullOrBlank()) {
                                                        signUpOtp = res.otpPreview
                                                    }
                                                    TactileFeedback.triggerSuccess(context)
                                                } catch (e: Exception) {
                                                    isSignUpOtpSentSuccess = false
                                                    signUpOtpStatusMessage = "Failed to send OTP: ${e.message}"
                                                    errorMessage = e.message
                                                } finally {
                                                    isSendingSignUpOtp = false
                                                }
                                            }
                                        }
                                    },
                                    enabled = !isSendingSignUpOtp,
                                    shape = RoundedCornerShape(14.dp),
                                    modifier = Modifier
                                        .height(56.dp)
                                        .testTag("send_otp_button"),
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = MaterialTheme.colorScheme.secondaryContainer,
                                        contentColor = MaterialTheme.colorScheme.onSecondaryContainer
                                    )
                                ) {
                                    if (isSendingSignUpOtp) {
                                        CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                                    } else {
                                        Icon(Icons.Default.Send, contentDescription = null, modifier = Modifier.size(14.dp))
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(if (isSignUpOtpSentSuccess) "Resend" else "Send OTP", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }

                            if (signUpOtpStatusMessage != null) {
                                Text(
                                    text = signUpOtpStatusMessage!!,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (isSignUpOtpSentSuccess) Color(0xFF10B981) else MaterialTheme.colorScheme.error,
                                    fontWeight = FontWeight.Medium
                                )
                            }

                            // 6-digit OTP input field
                            OutlinedTextField(
                                value = signUpOtp,
                                onValueChange = { if (it.length <= 6) signUpOtp = it },
                                label = { Text("Enter 6-Digit Email Code") },
                                placeholder = { Text("123456") },
                                leadingIcon = {
                                    Icon(Icons.Default.Key, contentDescription = null, tint = MaterialTheme.colorScheme.secondary)
                                },
                                singleLine = true,
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .testTag("signup_otp_input")
                            )
                        }

                        // 3. Security Password
                        OutlinedTextField(
                            value = signUpPassword,
                            onValueChange = { signUpPassword = it },
                            label = { Text("3. Security Password (Min 6 chars)") },
                            leadingIcon = {
                                Icon(Icons.Default.Lock, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            },
                            trailingIcon = {
                                IconButton(onClick = { isSignUpPasswordVisible = !isSignUpPasswordVisible }) {
                                    Icon(
                                        imageVector = if (isSignUpPasswordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                        contentDescription = null
                                    )
                                }
                            },
                            visualTransformation = if (isSignUpPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("signup_password_input")
                        )

                        // 4. Additional Info: Age, Level of Study, Course Pursued, Referral
                        HorizontalDivider(modifier = Modifier.padding(vertical = 4.dp))

                        Text(
                            text = "4. Additional Academic Information",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.secondary
                        )

                        // Age & Level of Study Row
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            OutlinedTextField(
                                value = signUpAge,
                                onValueChange = { if (it.length <= 3) signUpAge = it },
                                label = { Text("Age") },
                                singleLine = true,
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                shape = RoundedCornerShape(14.dp),
                                modifier = Modifier
                                    .width(85.dp)
                                    .testTag("signup_age_input")
                            )

                            // Level of Study Dropdown
                            Box(modifier = Modifier.weight(1f)) {
                                OutlinedTextField(
                                    value = signUpLevelOfStudy,
                                    onValueChange = {},
                                    readOnly = true,
                                    label = { Text("Level of Study") },
                                    trailingIcon = {
                                        IconButton(onClick = { isLevelDropdownExpanded = true }) {
                                            Icon(Icons.Default.ArrowDropDown, contentDescription = null)
                                        }
                                    },
                                    shape = RoundedCornerShape(14.dp),
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .testTag("signup_level_input")
                                )
                                DropdownMenu(
                                    expanded = isLevelDropdownExpanded,
                                    onDismissRequest = { isLevelDropdownExpanded = false }
                                ) {
                                    levelsList.forEach { level ->
                                        DropdownMenuItem(
                                            text = { Text(level, fontSize = 13.sp) },
                                            onClick = {
                                                signUpLevelOfStudy = level
                                                isLevelDropdownExpanded = false
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        // Course Pursued
                        OutlinedTextField(
                            value = signUpCoursePursued,
                            onValueChange = { signUpCoursePursued = it },
                            label = { Text("Course Pursued") },
                            placeholder = { Text("e.g. MBChB, Pharmacy, Nursing, Computer Science") },
                            leadingIcon = {
                                Icon(Icons.Default.School, contentDescription = null, tint = MaterialTheme.colorScheme.secondary)
                            },
                            singleLine = true,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("signup_course_input")
                        )

                        // Referral Link / Code
                        OutlinedTextField(
                            value = signUpReferralCode,
                            onValueChange = { signUpReferralCode = it },
                            label = { Text("Referral Link / Code (Optional)") },
                            placeholder = { Text("e.g. TRACE-REF-2026") },
                            leadingIcon = {
                                Icon(Icons.Default.Link, contentDescription = null, tint = MaterialTheme.colorScheme.secondary)
                            },
                            singleLine = true,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .testTag("signup_referral_input")
                        )

                        Spacer(modifier = Modifier.height(4.dp))

                        // Submit Create Account Button
                        Button(
                            onClick = {
                                val cleanName = signUpFullName.trim()
                                val cleanEmail = signUpEmail.trim()
                                val cleanOtp = signUpOtp.trim()
                                val cleanPass = signUpPassword.trim()
                                val ageInt = signUpAge.toIntOrNull()

                                if (cleanName.isBlank()) {
                                    errorMessage = "Please enter your Full Name."
                                } else if (cleanEmail.isBlank() || !cleanEmail.contains("@")) {
                                    errorMessage = "Please enter a valid email address."
                                } else if (cleanOtp.isBlank()) {
                                    errorMessage = "Please enter the 6-digit OTP sent to your email."
                                } else if (cleanPass.length < 6) {
                                    errorMessage = "Security password must be at least 6 characters."
                                } else {
                                    isLoading = true
                                    errorMessage = null
                                    scope.launch {
                                        try {
                                            val req = SignupRequest(
                                                fullName = cleanName,
                                                email = cleanEmail,
                                                password = cleanPass,
                                                otp = cleanOtp,
                                                age = ageInt,
                                                levelOfStudy = signUpLevelOfStudy,
                                                coursePursued = signUpCoursePursued.trim(),
                                                referralCode = signUpReferralCode.trim().ifEmpty { null },
                                                role = "Student"
                                            )
                                            val res = RetrofitClient.instance.signup(req)
                                            PreferenceManager.saveToken(context, res.accessToken)
                                            PreferenceManager.saveActiveUserId(context, res.userId)

                                            // Cache in Room DB
                                            val app = context.applicationContext as EduAIApplication
                                            val dao = app.database.dao()
                                            val passHash = hashPassword(cleanPass)
                                            val userEntity = UserEntity(
                                                id = res.userId,
                                                username = res.username,
                                                role = res.role,
                                                sensoryMode = "Visual",
                                                semesterStatus = signUpLevelOfStudy,
                                                aiPersona = "Socratic Mentor",
                                                email = cleanEmail,
                                                passwordHash = passHash,
                                                fullName = cleanName,
                                                age = ageInt,
                                                coursePursued = signUpCoursePursued.trim(),
                                                referralCode = signUpReferralCode.trim().ifEmpty { null }
                                            )
                                            dao.insertUser(userEntity)
                                            TactileFeedback.triggerSuccess(context)
                                            onLoginSuccess(res.role, res.userId)
                                        } catch (e: Exception) {
                                            errorMessage = "Enrollment error: ${e.message}"
                                        } finally {
                                            isLoading = false
                                        }
                                    }
                                }
                            },
                            enabled = !isLoading,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp)
                                .testTag("signup_submit_button")
                        ) {
                            if (isLoading) {
                                CircularProgressIndicator(modifier = Modifier.size(22.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimary)
                            } else {
                                Text("ENROLL & ENTER VAULT", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Browser Signup Link
            TextButton(
                onClick = {
                    val baseUrl = when (backendMode) {
                        "ngrok" -> "https://untropic-rozanne-noncomprehendingly.ngrok-free.dev/"
                        "container" -> "http://10.0.2.2:8001/"
                        else -> BuildConfig.BACKEND_BASE_URL
                    }
                    val signupUrl = baseUrl + "signup"
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(signupUrl))
                    context.startActivity(intent)
                }
            ) {
                Text("Open Web Signup Form in Browser ↗", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Backend Target Selector
            Text(
                text = "Backend Gateway Target",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.outline
            )
            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                val modes = listOf("cloud" to "Cloud", "ngrok" to "Ngrok", "container" to "Container")
                modes.forEach { (modeKey, modeName) ->
                    val isSelected = backendMode == modeKey
                    OutlinedButton(
                        onClick = {
                            backendMode = modeKey
                            PreferenceManager.saveBackendMode(context, modeKey)
                            PreferenceManager.saveDeveloperMode(context, modeKey != "cloud")
                        },
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
                            contentColor = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
                        ),
                        modifier = Modifier
                            .weight(1f)
                            .padding(horizontal = 4.dp)
                            .height(38.dp)
                    ) {
                        Text(modeName, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }

    // =================================================================
    // FORGOT PASSWORD MODAL DIALOG (Direct User Request Specifications)
    // =================================================================
    if (showForgotPasswordDialog) {
        AlertDialog(
            onDismissRequest = {
                if (!isResettingPassword) showForgotPasswordDialog = false
            },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.LockReset, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Reset Password", fontWeight = FontWeight.Black, fontSize = 18.sp)
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(
                        text = "Enter your registered email address to receive a secure one-time verification code (OTP) and set a new password.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    // Error in Dialog
                    if (forgotErrorMessage != null) {
                        Surface(
                            color = MaterialTheme.colorScheme.errorContainer,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = forgotErrorMessage!!,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                style = MaterialTheme.typography.labelSmall,
                                modifier = Modifier.padding(8.dp)
                            )
                        }
                    }

                    // Email with Send OTP Button
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedTextField(
                            value = forgotEmail,
                            onValueChange = { forgotEmail = it },
                            label = { Text("Account Email") },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .weight(1f)
                                .testTag("forgot_email_input")
                        )

                        Button(
                            onClick = {
                                val clean = forgotEmail.trim()
                                if (clean.isBlank() || !clean.contains("@")) {
                                    forgotErrorMessage = "Enter a valid email address."
                                } else {
                                    isSendingForgotOtp = true
                                    forgotErrorMessage = null
                                    forgotOtpStatusMessage = "Sending reset code..."
                                    scope.launch {
                                        try {
                                            val res = RetrofitClient.instance.sendOtp(
                                                SendOtpRequest(email = clean, action = "forgot_password")
                                            )
                                            forgotOtpStatusMessage = res.message + (res.otpPreview?.let { " [Code: $it]" } ?: "")
                                            if (!res.otpPreview.isNullOrBlank()) {
                                                forgotOtp = res.otpPreview
                                            }
                                            TactileFeedback.triggerSuccess(context)
                                        } catch (e: Exception) {
                                            forgotErrorMessage = e.message ?: "Failed to dispatch reset code."
                                            forgotOtpStatusMessage = null
                                        } finally {
                                            isSendingForgotOtp = false
                                        }
                                    }
                                }
                            },
                            enabled = !isSendingForgotOtp,
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier
                                .height(56.dp)
                                .testTag("forgot_send_otp_button")
                        ) {
                            if (isSendingForgotOtp) {
                                CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                            } else {
                                Text("Send OTP", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }

                    if (forgotOtpStatusMessage != null) {
                        Text(
                            text = forgotOtpStatusMessage!!,
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFF10B981),
                            fontWeight = FontWeight.Bold
                        )
                    }

                    // OTP Code Field
                    OutlinedTextField(
                        value = forgotOtp,
                        onValueChange = { if (it.length <= 6) forgotOtp = it },
                        label = { Text("6-Digit Verification Code") },
                        placeholder = { Text("123456") },
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("forgot_otp_input")
                    )

                    // New Password
                    OutlinedTextField(
                        value = forgotNewPassword,
                        onValueChange = { forgotNewPassword = it },
                        label = { Text("New Security Password (Min 6 chars)") },
                        visualTransformation = PasswordVisualTransformation(),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("forgot_new_password_input")
                    )

                    // Confirm Password
                    OutlinedTextField(
                        value = forgotConfirmPassword,
                        onValueChange = { forgotConfirmPassword = it },
                        label = { Text("Confirm New Password") },
                        visualTransformation = PasswordVisualTransformation(),
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("forgot_confirm_password_input")
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val cleanEmail = forgotEmail.trim()
                        val cleanOtp = forgotOtp.trim()
                        val cleanPass = forgotNewPassword.trim()
                        val confirmPass = forgotConfirmPassword.trim()

                        if (cleanEmail.isBlank() || !cleanEmail.contains("@")) {
                            forgotErrorMessage = "Please enter your registered email."
                        } else if (cleanOtp.isBlank()) {
                            forgotErrorMessage = "Please enter the 6-digit OTP code."
                        } else if (cleanPass.length < 6) {
                            forgotErrorMessage = "New password must be at least 6 characters."
                        } else if (cleanPass != confirmPass) {
                            forgotErrorMessage = "Passwords do not match."
                        } else {
                            isResettingPassword = true
                            forgotErrorMessage = null
                            scope.launch {
                                try {
                                    val req = ForgotPasswordResetRequest(
                                        email = cleanEmail,
                                        otp = cleanOtp,
                                        newPassword = cleanPass
                                    )
                                    val res = RetrofitClient.instance.resetPassword(req)
                                    Toast.makeText(context, res.message, Toast.LENGTH_LONG).show()

                                    // Pre-populate login form with updated credentials
                                    email = cleanEmail
                                    password = cleanPass
                                    successMessage = "Password reset successfully! You can now log in."
                                    showForgotPasswordDialog = false
                                    TactileFeedback.triggerSuccess(context)
                                } catch (e: Exception) {
                                    forgotErrorMessage = e.message ?: "Failed to reset password."
                                } finally {
                                    isResettingPassword = false
                                }
                            }
                        }
                    },
                    enabled = !isResettingPassword,
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.testTag("forgot_reset_submit_button")
                ) {
                    if (isResettingPassword) {
                        CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                    } else {
                        Text("Reset Password", fontWeight = FontWeight.Bold)
                    }
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { showForgotPasswordDialog = false },
                    enabled = !isResettingPassword
                ) {
                    Text("Cancel")
                }
            },
            shape = RoundedCornerShape(20.dp)
        )
    }
}
