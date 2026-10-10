
// IDENTITY: repository/EduAIRepository.kt
package com.example.edu_ai.repository

import com.example.edu_ai.data.local.*
import com.example.edu_ai.data.remote.EduAIApi
import com.example.edu_ai.data.remote.TeacherDashboardResponse
import com.example.edu_ai.data.remote.ClassReportResponse
import com.example.edu_ai.data.remote.ApiTimetableResponse
import com.example.edu_ai.utils.PreferenceManager
import android.content.Context
import com.google.gson.Gson
import kotlinx.coroutines.flow.*

class EduAIRepository(
    private val api: EduAIApi,
    val dao: EduAIDao
) {
    private val gson = Gson()

    suspend fun logout(context: Context) {
        PreferenceManager.clearToken(context)
        PreferenceManager.clearActiveUserId(context)
    }

    suspend fun insertUserPreservingCredentials(user: UserEntity) {
        val existing = dao.getUserById(user.id)
        if (existing != null) {
            dao.insertUser(user.copy(
                email = existing.email ?: user.email,
                passwordHash = existing.passwordHash ?: user.passwordHash
            ))
        } else {
            dao.insertUser(user)
        }
    }

    fun getDashboardData(userId: String): Flow<UserEntity?> = flow {
        try {
            // First sanitize any corrupted cache and remove any duplicate hierarchy nodes
            dao.sanitizeCorruptedCachedContent()
            dao.deduplicateUnits()
            dao.deduplicateModules()
            dao.deduplicateTopics()
            dao.deduplicateSubtopics()
            dao.deduplicateQuizHistory()
            dao.deletePlaceholderUnitsIfUnused()

            val response = api.getDashboard(userId)
            
            val userEntity = UserEntity(
                id = userId,
                username = response.username ?: userId,
                role = response.role ?: "Student",
                sensoryMode = response.sensoryMode ?: "Visual",
                semesterStatus = response.semesterStatus ?: "Active",
                aiPersona = response.aiPersona ?: "Socratic Mentor"
            )
            insertUserPreservingCredentials(userEntity)
            
            // Sync full hierarchy from backend if available using persistent non-destructive merge
            if (response.units != null) {
                response.units.forEach { apiUnit ->
                    // 1. Direct Unit Lookup by Name
                    val existingUnit = dao.getUnitByName(apiUnit.name)
                    val unitId = if (existingUnit != null) {
                        existingUnit.localId
                    } else {
                        dao.insertUnits(listOf(UnitEntity(unitName = apiUnit.name, isActive = apiUnit.isActive))).first()
                    }

                    apiUnit.modules.forEach { apiModule ->
                        // 2. Direct Module Lookup by Unit and Name
                        val existingModule = dao.getModuleByName(unitId, apiModule.name)
                        val moduleId = if (existingModule != null) {
                            existingModule.moduleId
                        } else {
                            dao.insertModules(listOf(ModuleEntity(unitId = unitId, name = apiModule.name))).first()
                        }

                        apiModule.topics.forEach { apiTopic ->
                            // 3. Direct Topic Lookup by Module and Name
                            val existingTopic = dao.getTopicByName(moduleId, apiTopic.name)
                            val topicId = if (existingTopic != null) {
                                existingTopic.topicId
                            } else {
                                dao.insertTopics(listOf(TopicEntity(moduleId = moduleId, name = apiTopic.name))).first()
                            }

                            apiTopic.subtopics.forEach { apiSubtopic ->
                                // 4. Direct Subtopic Lookup by Topic and Name
                                val existingSubtopic = dao.getSubtopicByName(topicId, apiSubtopic.name) 
                                    ?: dao.getSubtopicByTitle(apiSubtopic.name)

                                if (existingSubtopic != null) {
                                    // NEVER reset an already-completed subtopic to false!
                                    val shouldMarkCompleted = existingSubtopic.isCompleted || apiSubtopic.isCompleted
                                    val objectivesList = apiSubtopic.learningObjectives.map { it.description }
                                    val objectivesJson = gson.toJson(objectivesList)
                                    
                                    // Only update if objectives were missing or backend completed it
                                    if (existingSubtopic.learningObjectivesJson.isNullOrBlank() || (!existingSubtopic.isCompleted && apiSubtopic.isCompleted)) {
                                        dao.insertSubtopics(listOf(existingSubtopic.copy(
                                            isCompleted = shouldMarkCompleted,
                                            learningObjectivesJson = if (existingSubtopic.learningObjectivesJson.isNullOrBlank()) objectivesJson else existingSubtopic.learningObjectivesJson
                                        )))
                                    }
                                } else {
                                    val objectivesList = apiSubtopic.learningObjectives.map { it.description }
                                    dao.insertSubtopics(listOf(
                                        SubtopicEntity(
                                            topicId = topicId,
                                            name = apiSubtopic.name,
                                            isCompleted = apiSubtopic.isCompleted,
                                            learningObjectivesJson = gson.toJson(objectivesList)
                                        )
                                    ))
                                }
                            }
                        }
                    }
                }
            } else {
                val activeUnits = response.activeUnits ?: emptyList()
                activeUnits.forEach { unitName ->
                    val existingUnit = dao.getUnitByName(unitName)
                    if (existingUnit == null) {
                        dao.insertUnits(listOf(UnitEntity(unitName = unitName, isActive = true)))
                    }
                }
            }

            // Sync quiz history without creating duplicates
            val currentLocalHistory = dao.getQuizHistory(userId).first()
            response.quizHistory?.forEach { q ->
                val qName = q.unitName ?: "General"
                val score = q.pnl ?: 0.0
                val ts = q.timestamp?.toLongOrNull() ?: 0L
                
                val existingHistory = currentLocalHistory.find { 
                    it.unitName.equals(qName, ignoreCase = true) && 
                    (if (ts > 0L) it.timestamp == ts else kotlin.math.abs(it.pnlScore - score) < 0.1)
                }
                if (existingHistory == null) {
                    dao.insertQuizHistory(
                        QuizHistoryEntity(
                            userId = userId,
                            unitName = qName,
                            pnlScore = score,
                            timestamp = if (ts > 0L) ts else System.currentTimeMillis()
                        )
                    )
                }
            }
            dao.deduplicateQuizHistory()

            emit(userEntity)
        } catch (e: Exception) {
            val cachedUser = dao.getUserById(userId)
            if (cachedUser != null) {
                emit(cachedUser)
            } else {
                // Fallback for dev/offline first time ONLY if local database is completely empty
                val devUser = UserEntity(
                    id = userId,
                    username = userId,
                    role = "Student",
                    sensoryMode = "Visual",
                    semesterStatus = "Year 4 - Medical Candidate",
                    aiPersona = "Socratic Mentor"
                )
                dao.insertUser(devUser)

                // Do not populate default placeholder units (Biochemistry, General Surgery, Internal Medicine)
                // New users start with a clean dashboard and can add authentic units from the Curriculum Catalogue.
                dao.deletePlaceholderUnitsIfUnused()

                emit(devUser)
            }
        }
    }

    suspend fun buildStudyContext(userId: String): com.example.edu_ai.data.remote.ApiStudyContextPayload {
        val quizHistory = dao.getQuizHistory(userId).firstOrNull() ?: emptyList()
        val totalQuizzes = quizHistory.size
        val avgScore = if (totalQuizzes > 0) {
            (quizHistory.sumOf { it.pnlScore } / totalQuizzes).toFloat()
        } else null

        val weakTopics = quizHistory.filter { it.pnlScore < 70.0 }.map { it.unitName }.distinct()
        val masteredTopics = quizHistory.filter { it.pnlScore >= 80.0 }.map { it.unitName }.distinct()
        val recentQuizzes = quizHistory.take(5).map {
            com.example.edu_ai.data.remote.ApiQuizAttemptInfo(
                unitName = it.unitName,
                score = it.pnlScore.toFloat(),
                timestamp = it.timestamp
            )
        }

        val unitsWithModules = dao.getAllUnitsWithModules().firstOrNull() ?: emptyList()
        val allSubtopics = unitsWithModules.flatMap { it.modules }.flatMap { it.topics }.flatMap { it.subtopics }
        val completedSubtopics = allSubtopics.filter { it.isCompleted }.map { it.name }
        val pendingSubtopics = allSubtopics.filter { !it.isCompleted }.map { it.name }

        val overallProgress = if (allSubtopics.isNotEmpty()) {
            (completedSubtopics.size.toFloat() / allSubtopics.size.toFloat()) * 100f
        } else 0f

        val unitsProgress = unitsWithModules.map { uWithM ->
            val subs = uWithM.modules.flatMap { it.topics }.flatMap { it.subtopics }
            val completed = subs.count { it.isCompleted }
            val pct = if (subs.isNotEmpty()) (completed.toFloat() / subs.size.toFloat()) * 100f else 0f
            com.example.edu_ai.data.remote.ApiUnitProgressInfo(
                unitName = uWithM.unit.unitName,
                completedSubtopics = completed,
                totalSubtopics = subs.size,
                progressPercentage = pct
            )
        }

        return com.example.edu_ai.data.remote.ApiStudyContextPayload(
            overallProgressPercentage = overallProgress,
            unitsProgress = unitsProgress,
            completedSubtopicNames = completedSubtopics,
            pendingSubtopicNames = pendingSubtopics,
            averageQuizScore = avgScore,
            totalQuizzesTaken = totalQuizzes,
            masteredTopics = masteredTopics,
            weakTopics = weakTopics,
            recentQuizzes = recentQuizzes
        )
    }

    suspend fun getWeeklyTimetable(
        userId: String,
        studyContext: com.example.edu_ai.data.remote.ApiStudyContextPayload? = null,
        forceRefresh: Boolean = false
    ): ApiTimetableResponse {
        val cachedTimetable = dao.getTimetableByUserId(userId)
        val oneWeekInMillis = 7 * 24 * 60 * 60 * 1000L
        
        // Only request a new timetable if forceRefresh is true, or if 1 week has passed
        if (!forceRefresh && cachedTimetable != null && (System.currentTimeMillis() - cachedTimetable.timestamp) < oneWeekInMillis) {
            // Return cached version
            return ApiTimetableResponse(
                weeklyPlan = gson.fromJson(cachedTimetable.weeklyPlanJson, Array<com.example.edu_ai.data.remote.ApiTimetableSlot>::class.java).toList(),
                aiBrief = cachedTimetable.aiBrief
            )
        }

        // Fetch fresh from AI using real-time user learning progress and quiz metrics
        val contextToSend = studyContext ?: buildStudyContext(userId)

        return try {
            val freshTimetable = api.getTimetableWithContext(userId, contextToSend)
            // Cache it
            dao.insertTimetable(
                TimetableEntity(
                    userId = userId,
                    weeklyPlanJson = gson.toJson(freshTimetable.weeklyPlan),
                    aiBrief = freshTimetable.aiBrief,
                    timestamp = System.currentTimeMillis()
                )
            )
            freshTimetable
        } catch (e: Exception) {
            // If context endpoint fails or network offline, try standard endpoint
            try {
                val fallbackTimetable = api.getTimetable(userId)
                dao.insertTimetable(
                    TimetableEntity(
                        userId = userId,
                        weeklyPlanJson = gson.toJson(fallbackTimetable.weeklyPlan),
                        aiBrief = fallbackTimetable.aiBrief,
                        timestamp = System.currentTimeMillis()
                    )
                )
                fallbackTimetable
            } catch (e2: Exception) {
                // If API fails but we have an old cache, return it anyway
                if (cachedTimetable != null) {
                    ApiTimetableResponse(
                        weeklyPlan = gson.fromJson(cachedTimetable.weeklyPlanJson, Array<com.example.edu_ai.data.remote.ApiTimetableSlot>::class.java).toList(),
                        aiBrief = cachedTimetable.aiBrief
                    )
                } else {
                    throw e2
                }
            }
        }
    }

    // --- Teacher Methods ---
    suspend fun getTeacherDashboard(): TeacherDashboardResponse = api.getTeacherDashboard()
    suspend fun generateClassReport(): ClassReportResponse = api.generateClassReport()
    suspend fun updateStudentProfile(userId: String, updates: Map<String, Any?>) = api.updateStudentProfile(userId, updates)
    suspend fun sendProgressReport(studentId: String) = api.sendProgressReport(studentId)

    // --- Parent Methods ---
    suspend fun getParentDashboard(studentId: String) = api.getParentDashboard(studentId)

    // --- Ingestion / Library Methods ---
    suspend fun getLibraryUnits() = api.getLibraryUnits()
    suspend fun addUnitToUser(unitId: Int, userId: String) = api.addUnitToUser(unitId, userId)

    // --- Bookmarking & Synchronization Methods ---

    fun getLocalBookmarks(userId: String): Flow<List<BookmarkEntity>> = dao.getBookmarks(userId)

    suspend fun deleteLocalBookmark(bookmarkId: String) {
        dao.deleteBookmark(bookmarkId)
    }

    suspend fun saveBookmarkAndSync(
        userId: String,
        type: String,
        title: String,
        target: String,
        context: String,
        notes: String?
    ) {
        val id = "bm-${System.currentTimeMillis()}"
        val entity = BookmarkEntity(
            id = id,
            userId = userId,
            type = type,
            title = title,
            target = target,
            context = context,
            timestamp = System.currentTimeMillis(),
            notes = notes
        )
        dao.insertBookmark(entity)
        try {
            val apiItem = com.example.edu_ai.data.remote.ApiBookmarkItem(
                id = id,
                type = type,
                title = title,
                target = target,
                context = context,
                timestamp = System.currentTimeMillis() / 1000.0,
                notes = notes
            )
            api.saveBookmark(userId, apiItem)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    suspend fun updateSubtopicStatusAndSync(userId: String, subtopicId: Long, isCompleted: Boolean) {
        dao.updateSubtopicStatus(subtopicId, isCompleted)
        try {
            val progressItem = com.example.edu_ai.data.remote.ApiProgressItem(
                nodeId = subtopicId.toInt(),
                nodeType = "subtopic",
                status = if (isCompleted) "Completed" else "Unlocked",
                lastStudiedAt = System.currentTimeMillis() / 1000.0
            )
            api.sendSyncData(
                userId = userId,
                request = com.example.edu_ai.data.remote.ApiSyncRequest(progress = listOf(progressItem))
            )
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    suspend fun triggerSync(userId: String) {
        try {
            // First push any locally completed subtopics to server so server never loses progress
            val completedLocal = dao.getCompletedSubtopics()
            if (completedLocal.isNotEmpty()) {
                try {
                    val progressItems = completedLocal.map { sub ->
                        com.example.edu_ai.data.remote.ApiProgressItem(
                            nodeId = sub.subtopicId.toInt(),
                            nodeType = "subtopic",
                            status = "Completed",
                            lastStudiedAt = System.currentTimeMillis() / 1000.0
                        )
                    }
                    api.sendSyncData(userId, com.example.edu_ai.data.remote.ApiSyncRequest(progress = progressItems))
                } catch (e: Exception) {
                    // Ignore transient push errors
                }
            }

            val response = api.getSyncData(userId)

            // 1. Update local progress status from server without overwriting existing completions
            response.progress.forEach { item ->
                if (item.nodeType == "subtopic") {
                    val isComp = item.status == "Completed"
                    if (isComp) {
                        dao.updateSubtopicStatus(item.nodeId.toLong(), true)
                    }
                }
            }

            // 2. Load bookmarks from server
            val bookmarksToInsert = response.bookmarks.map { b ->
                BookmarkEntity(
                    id = b.id ?: "bm-${System.currentTimeMillis()}-${(100..999).random()}",
                    userId = userId,
                    type = b.type,
                    title = b.title,
                    target = b.target,
                    context = b.context,
                    timestamp = (b.timestamp * 1000).toLong(),
                    notes = b.notes
                )
            }
            if (bookmarksToInsert.isNotEmpty()) {
                dao.insertBookmarks(bookmarksToInsert)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    // --- System Releases & Mandatory Upgrade Methods ---

    suspend fun getSystemReleases(clientVersionCode: Int): com.example.edu_ai.data.remote.ApiReleasesResponse {
        return api.getSystemReleases(clientVersionCode)
    }

    suspend fun createRelease(request: com.example.edu_ai.data.remote.CreateReleaseRequest): Map<String, Any?> {
        return api.createRelease(request)
    }

    suspend fun toggleMandatoryRelease(releaseId: Long): Map<String, Any?> {
        return api.toggleMandatoryRelease(releaseId)
    }

    // --- Auth & Verification OTP Methods ---

    suspend fun sendOtp(email: String, action: String = "signup"): com.example.edu_ai.schemas.SendOtpResponse {
        return api.sendOtp(com.example.edu_ai.schemas.SendOtpRequest(email = email, action = action))
    }

    suspend fun verifyOtp(email: String, otp: String, action: String = "signup"): com.example.edu_ai.schemas.GenericAuthResponse {
        return api.verifyOtp(com.example.edu_ai.schemas.VerifyOtpRequest(email = email, otp = otp, action = action))
    }

    suspend fun signup(request: com.example.edu_ai.schemas.SignupRequest): com.example.edu_ai.schemas.TokenResponse {
        return api.signup(request)
    }

    suspend fun resetPassword(request: com.example.edu_ai.schemas.ForgotPasswordResetRequest): com.example.edu_ai.schemas.GenericAuthResponse {
        return api.resetPassword(request)
    }
}


 