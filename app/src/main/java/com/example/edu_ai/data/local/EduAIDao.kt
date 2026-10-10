
// IDENTITY: data/local/EduAIDao.kt
package com.example.edu_ai.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface EduAIDao {

    // User
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: UserEntity)

    @Query("SELECT * FROM users LIMIT 1")
    fun getUser(): Flow<UserEntity?>

    @Query("SELECT * FROM users WHERE id = :userId")
    fun getUserFlow(userId: String): Flow<UserEntity?>
    
    @Query("SELECT * FROM users WHERE id = :userId")
    suspend fun getUserById(userId: String): UserEntity?

    @Query("SELECT * FROM users WHERE email = :email OR username = :email LIMIT 1")
    suspend fun getUserByEmailOrUsername(email: String): UserEntity?

    @Query("DELETE FROM users")
    suspend fun clearUsers()

    // Units
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUnits(units: List<UnitEntity>): List<Long>

    @Query("SELECT * FROM units")
    fun getAllUnits(): Flow<List<UnitEntity>>

    @Transaction
    @Query("SELECT * FROM units")
    fun getAllUnitsWithModules(): Flow<List<UnitWithModules>>

    @Query("DELETE FROM units")
    suspend fun deleteAllUnits()

    @Query("DELETE FROM units WHERE localId = :unitId")
    suspend fun deleteUnitById(unitId: Long)

    @Query("DELETE FROM units WHERE unitName IN ('Biochemistry II', 'General Surgery', 'Internal Medicine') AND localId NOT IN (SELECT unitId FROM modules WHERE moduleId IN (SELECT moduleId FROM topics WHERE topicId IN (SELECT topicId FROM subtopics WHERE isCompleted = 1)))")
    suspend fun deletePlaceholderUnitsIfUnused()

    // Modules
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertModules(modules: List<ModuleEntity>): List<Long>

    @Query("SELECT * FROM modules WHERE unitId = :unitId")
    fun getModulesForUnit(unitId: Long): Flow<List<ModuleEntity>>

    // Topics
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTopics(topics: List<TopicEntity>): List<Long>

    @Query("SELECT * FROM topics WHERE moduleId = :moduleId")
    fun getTopicsForModule(moduleId: Long): Flow<List<TopicEntity>>

    // Subtopics
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubtopics(subtopics: List<SubtopicEntity>): List<Long>

    @Query("SELECT * FROM subtopics WHERE topicId = :topicId")
    fun getSubtopicsForTopic(topicId: Long): Flow<List<SubtopicEntity>>

    @Query("UPDATE subtopics SET isCompleted = :isCompleted WHERE subtopicId = :subtopicId")
    suspend fun updateSubtopicStatus(subtopicId: Long, isCompleted: Boolean)

    @Query("UPDATE subtopics SET cachedContentJson = :cachedContentJson WHERE subtopicId = :subtopicId")
    suspend fun updateSubtopicCachedContent(subtopicId: Long, cachedContentJson: String?)

    @Query("UPDATE subtopics SET cachedQuizJson = :cachedQuizJson WHERE subtopicId = :subtopicId")
    suspend fun updateSubtopicCachedQuiz(subtopicId: Long, cachedQuizJson: String?)

    @Query("UPDATE units SET cachedQuizJson = :cachedQuizJson WHERE localId = :localId")
    suspend fun updateUnitCachedQuiz(localId: Long, cachedQuizJson: String?)

    @Query("SELECT * FROM subtopics WHERE subtopicId = :subtopicId LIMIT 1")
    suspend fun getSubtopicById(subtopicId: Long): SubtopicEntity?

    @Query("""
        SELECT u.unitName FROM units u
        INNER JOIN modules m ON m.unitId = u.localId
        INNER JOIN topics t ON t.moduleId = m.moduleId
        INNER JOIN subtopics s ON s.topicId = t.topicId
        WHERE s.subtopicId = :subtopicId LIMIT 1
    """)
    suspend fun getUnitNameBySubtopicId(subtopicId: Long): String?

    @Query("SELECT * FROM units WHERE unitName = :name LIMIT 1")
    suspend fun getUnitByName(name: String): UnitEntity?

    @Query("SELECT * FROM modules WHERE unitId = :unitId AND name = :name LIMIT 1")
    suspend fun getModuleByName(unitId: Long, name: String): ModuleEntity?

    @Query("SELECT * FROM topics WHERE moduleId = :moduleId AND name = :name LIMIT 1")
    suspend fun getTopicByName(moduleId: Long, name: String): TopicEntity?

    @Query("SELECT * FROM subtopics WHERE topicId = :topicId AND name = :name LIMIT 1")
    suspend fun getSubtopicByName(topicId: Long, name: String): SubtopicEntity?

    @Query("SELECT * FROM subtopics WHERE name = :name LIMIT 1")
    suspend fun getSubtopicByTitle(name: String): SubtopicEntity?

    @Query("UPDATE subtopics SET isCompleted = 1 WHERE name = :name")
    suspend fun markSubtopicCompletedByName(name: String)

    @Query("SELECT * FROM subtopics WHERE isCompleted = 1")
    suspend fun getCompletedSubtopics(): List<SubtopicEntity>

    @Query("DELETE FROM units WHERE localId NOT IN (SELECT MIN(localId) FROM units GROUP BY unitName)")
    suspend fun deduplicateUnits()

    @Query("DELETE FROM modules WHERE moduleId NOT IN (SELECT MIN(moduleId) FROM modules GROUP BY unitId, name)")
    suspend fun deduplicateModules()

    @Query("DELETE FROM topics WHERE topicId NOT IN (SELECT MIN(topicId) FROM topics GROUP BY moduleId, name)")
    suspend fun deduplicateTopics()

    @Query("DELETE FROM subtopics WHERE subtopicId NOT IN (SELECT MIN(subtopicId) FROM subtopics GROUP BY topicId, name)")
    suspend fun deduplicateSubtopics()

    @Query("UPDATE subtopics SET cachedContentJson = NULL WHERE cachedContentJson LIKE '%consultation failed%' OR cachedContentJson LIKE '%failed to reconnect%'")
    suspend fun sanitizeCorruptedCachedContent()

    // Quiz History
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuizHistory(quiz: QuizHistoryEntity)

    @Query("SELECT * FROM quiz_history WHERE userId = :userId ORDER BY timestamp DESC")
    fun getQuizHistory(userId: String): Flow<List<QuizHistoryEntity>>

    @Query("DELETE FROM quiz_history WHERE localId NOT IN (SELECT MIN(localId) FROM quiz_history GROUP BY userId, unitName, pnlScore)")
    suspend fun deduplicateQuizHistory()

    @Query("DELETE FROM quiz_history")
    suspend fun clearAllQuizHistory()

    // Chat Sessions
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChatSession(session: ChatSessionEntity): Long

    @Update
    suspend fun updateChatSession(session: ChatSessionEntity)

    @Query("SELECT * FROM chat_sessions WHERE userId = :userId AND isArchived = 0 ORDER BY timestamp DESC LIMIT 1")
    suspend fun getActiveSession(userId: String): ChatSessionEntity?

    @Query("SELECT * FROM chat_sessions WHERE userId = :userId AND isArchived = 1 ORDER BY timestamp DESC")
    fun getArchivedSessions(userId: String): Flow<List<ChatSessionEntity>>

    @Query("UPDATE chat_sessions SET isArchived = 1 WHERE userId = :userId AND isArchived = 0")
    suspend fun archiveActiveSessions(userId: String)

    @Query("DELETE FROM chat_sessions WHERE id = :sessionId")
    suspend fun deleteSession(sessionId: Int)

    @Query("DELETE FROM chat_sessions")
    suspend fun clearAllChatSessions()

    // Chat Messages
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChatMessage(message: ChatMessageEntity)

    @Query("SELECT * FROM chat_messages WHERE sessionId = :sessionId ORDER BY timestamp ASC")
    fun getChatMessagesBySession(sessionId: Int): Flow<List<ChatMessageEntity>>

    @Query("DELETE FROM chat_messages WHERE sessionId = :sessionId")
    suspend fun clearSessionMessages(sessionId: Int)

    @Query("DELETE FROM chat_messages")
    suspend fun clearAllChatHistory()

    // Timetable
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTimetable(timetable: TimetableEntity)

    @Query("SELECT * FROM timetables WHERE userId = :userId")
    suspend fun getTimetableByUserId(userId: String): TimetableEntity?

    @Query("DELETE FROM timetables WHERE userId = :userId")
    suspend fun deleteTimetable(userId: String)

    @Query("DELETE FROM timetables")
    suspend fun clearAllTimetables()

    // Notes
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertNote(note: NoteEntity)

    @Update
    suspend fun updateNote(note: NoteEntity)

    @Query("SELECT * FROM notes WHERE userId = :userId ORDER BY lastUpdated DESC")
    fun getAllNotes(userId: String): Flow<List<NoteEntity>>

    @Query("SELECT * FROM notes WHERE sessionId = :sessionId LIMIT 1")
    suspend fun getNoteBySession(sessionId: Int): NoteEntity?

    @Query("DELETE FROM notes WHERE id = :noteId")
    suspend fun deleteNote(noteId: Int)

    @Query("DELETE FROM notes")
    suspend fun clearAllNotes()

    // Bookmarks
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBookmark(bookmark: BookmarkEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBookmarks(bookmarks: List<BookmarkEntity>)

    @Query("SELECT * FROM bookmarks WHERE userId = :userId ORDER BY timestamp DESC")
    fun getBookmarks(userId: String): Flow<List<BookmarkEntity>>

    @Query("DELETE FROM bookmarks WHERE id = :bookmarkId")
    suspend fun deleteBookmark(bookmarkId: String)

    @Query("DELETE FROM bookmarks")
    suspend fun clearAllBookmarks()

    // App Releases Archive
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRelease(release: AppReleaseEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReleases(releases: List<AppReleaseEntity>)

    @Query("SELECT * FROM app_releases ORDER BY versionCode DESC, timestamp DESC")
    fun getReleases(): Flow<List<AppReleaseEntity>>

    @Query("SELECT * FROM app_releases WHERE isMandatory = 1 ORDER BY versionCode DESC LIMIT 1")
    fun getLatestMandatoryRelease(): Flow<AppReleaseEntity?>

    @Query("UPDATE app_releases SET isMandatory = :isMandatory WHERE id = :id")
    suspend fun updateReleaseMandatoryStatus(id: Long, isMandatory: Boolean)

    @Query("DELETE FROM app_releases WHERE id = :id")
    suspend fun deleteRelease(id: Long)
}


 