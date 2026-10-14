package com.example.edu_ai.ui.screens.student

import androidx.compose.animation.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.BorderColor
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.FormatPaint
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.edu_ai.data.local.BookmarkEntity
import com.example.edu_ai.data.local.SubtopicEntity
import com.example.edu_ai.data.model.HighlightColor
import com.example.edu_ai.data.model.TextHighlight
import com.example.edu_ai.data.remote.ChatRequest
import com.example.edu_ai.ui.components.DynamicBackground
import com.example.edu_ai.ui.components.FormattedText
import com.example.edu_ai.ui.components.HighlighterBar
import com.example.edu_ai.ui.components.QuickAddHighlightDialog
import com.example.edu_ai.ui.components.ManageHighlightsBottomSheet
import com.example.edu_ai.utils.HighlightManager
import com.example.edu_ai.utils.ExplanationVersion
import com.example.edu_ai.utils.PreferenceManager
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LearnScreen(
    userId: String,
    subtopicId: Long,
    onBack: () -> Unit,
    onNavigateToBrowser: (String) -> Unit,
    onNavigateToQuiz: (unitName: String, subtopicName: String) -> Unit = { _, _ -> },
    studentViewModel: StudentViewModel = viewModel(factory = StudentViewModel.Factory)
) {
    val uiState by studentViewModel.uiState.collectAsState()
    val scope = rememberCoroutineScope()
    val gson = remember { com.google.gson.Gson() }
    val context = androidx.compose.ui.platform.LocalContext.current

    // Load subtopic directly from SQLite database to preserve local cached content and learning objectives
    var dbSubtopic by remember { mutableStateOf<SubtopicEntity?>(null) }
    var dbSubtopicUnitName by remember { mutableStateOf<String?>(null) }
    var showQuizPromptDialog by remember { mutableStateOf(false) }
    var isHighlighterBarOpen by remember { mutableStateOf(false) }
    var selectedHighlightColor by remember { mutableStateOf(HighlightColor.YELLOW) }
    var subtopicHighlights by remember { mutableStateOf<List<TextHighlight>>(emptyList()) }
    var showAddHighlightDialog by remember { mutableStateOf(false) }
    var showManageHighlightsDialog by remember { mutableStateOf(false) }

    val inquiries = remember { mutableStateListOf<InquiryItem>() }

    LaunchedEffect(subtopicId) {
        dbSubtopic = studentViewModel.getSubtopicById(subtopicId)
        dbSubtopicUnitName = studentViewModel.getUnitNameBySubtopicId(subtopicId)
        subtopicHighlights = HighlightManager.getHighlights(context, subtopicId)

        // Load persistent inquiries
        val inquiriesJson = com.example.edu_ai.utils.PreferenceManager.getSubtopicInquiries(context, subtopicId)
        inquiries.clear()
        if (!inquiriesJson.isNullOrBlank()) {
            try {
                val listType = object : com.google.gson.reflect.TypeToken<List<InquiryItem>>() {}.type
                val savedList = gson.fromJson<List<InquiryItem>>(inquiriesJson, listType)
                if (savedList != null) {
                    inquiries.addAll(savedList)
                }
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    // Find subtopic from memory state
    var targetSubtopic: SubtopicEntity? = null
    var targetUnitName = "Clinical Science"
    
    for (unitWithMod in uiState.unitsWithModules) {
        for (modWithTop in unitWithMod.modules) {
            for (topWithSub in modWithTop.topics) {
                val found = topWithSub.subtopics.find { it.subtopicId == subtopicId }
                if (found != null) {
                    targetSubtopic = found
                    targetUnitName = unitWithMod.unit.unitName
                    break
                }
            }
        }
    }

    val memorySubtopic = targetSubtopic ?: SubtopicEntity(
        subtopicId = subtopicId,
        topicId = 0L,
        name = "Regulation of PFK-1 in Erythrocytes",
        isCompleted = false
    )

    val subtopic = dbSubtopic ?: memorySubtopic

    // Dynamic study notes cache
    val studyNotes = remember { mutableStateMapOf<Int, String>() }
    val studyLoading = remember { mutableStateMapOf<Int, Boolean>() }
    val studyErrors = remember { mutableStateMapOf<Int, String?>() }

    // Educational Slide Objectives - Formulated dynamically based on subtopic learning objectives
    val parsedObjectives = remember(subtopic) {
        val json = subtopic.learningObjectivesJson
        if (!json.isNullOrBlank()) {
            try {
                val listType = object : com.google.gson.reflect.TypeToken<List<String>>() {}.type
                val list = gson.fromJson<List<String>>(json, listType)
                if (!list.isNullOrEmpty()) {
                    list.mapIndexed { idx, desc ->
                        SyllabusObjective(
                            title = "Learning Objective ${idx + 1}",
                            description = desc,
                            prompt = "Teach me the concepts to fulfill the learning objective: '$desc' regarding '${subtopic.name}'. Educational instruction: Start with foundational concepts, basic definitions, and core principles first, then nicely and systematically work your way up to intermediate mechanisms, major concepts, and clinical applications. Structure with clear high-yield bullet points, formatting highlights, and YouTube / web video recommendations."
                        )
                    }
                } else null
            } catch (e: Exception) {
                null
            }
        } else null
    }

    val objectives = parsedObjectives ?: remember(subtopic.name) {
        listOf(
            SyllabusObjective(
                title = "Foundational Concepts & Core Principles",
                description = "Basic definitions, essential physiological baselines, and fundamental principles of ${subtopic.name}.",
                prompt = "Teach me the foundational concepts, core definitions, and basic principles of '${subtopic.name}'. Start with the ground-level fundamentals and intuitive baselines to establish a strong foundation before advancing to complex mechanics. Structure with high-yield bullet points, clear explanations, and introductory video/reference recommendations."
            ),
            SyllabusObjective(
                title = "Mechanisms & System Dynamics",
                description = "Cellular pathophysiology, biochemical pathways, and intermediate system interactions.",
                prompt = "Building directly upon the foundational principles of '${subtopic.name}', explain the intermediate mechanisms, cellular pathophysiology, biochemical regulation, and system dynamics. Connect the fundamental principles to how the system functions in normal and altered states with diagrams and clear bullet points."
            ),
            SyllabusObjective(
                title = "Major Concepts & Clinical Synthesis",
                description = "Major overarching concepts, clinical presentations, diagnostic criteria, and high-yield exam pearls.",
                prompt = "Now synthesize the major concepts, clinical presentations, diagnostic protocols, and high-yield exam pearls for '${subtopic.name}'. Work up to advanced clinical management, common diagnostic traps, and comprehensive mastery with clinical tables and high-yield video references."
            )
        )
    }

    var isStudyingStarted by remember { mutableStateOf(false) }
    var currentStep by remember { mutableIntStateOf(0) }
    var bookmarkNote by remember { mutableStateOf("") }
    var showBookmarkDialog by remember { mutableStateOf(false) }
    var isBookmarked by remember { mutableStateOf(false) }

    // Chat AI state
    var aiQuestion by remember { mutableStateOf("") }
    var aiResponse by remember { mutableStateOf<String?>(null) }
    var isAiLoading by remember { mutableStateOf(false) }

    // Explanation Versions & Redo State for covered subtopic areas
    val explanationVersions = remember { mutableStateMapOf<Int, List<ExplanationVersion>>() }
    val activeVersionIndex = remember { mutableStateMapOf<Int, Int>() }
    var showOlderVersionsDialog by remember { mutableStateOf(false) }

    fun refreshVersionsForStep(step: Int, currentNoteText: String? = null) {
        val saved = PreferenceManager.getSubtopicExplanationVersions(context, subtopicId, step).toMutableList()
        val note = currentNoteText ?: studyNotes[step]
        if (saved.isEmpty() && !note.isNullOrBlank()) {
            val v1 = ExplanationVersion(
                versionNumber = 1,
                content = note,
                tag = "Original Explanation"
            )
            val updated = PreferenceManager.saveSubtopicExplanationVersion(context, subtopicId, step, v1)
            explanationVersions[step] = updated
            activeVersionIndex[step] = 0
        } else {
            explanationVersions[step] = saved
            if (activeVersionIndex[step] == null || (activeVersionIndex[step] ?: 0) >= saved.size) {
                activeVersionIndex[step] = (saved.size - 1).coerceAtLeast(0)
            }
        }
    }

    fun redoExplanationForStep(step: Int) {
        val existing = explanationVersions[step] ?: emptyList()
        val nextVer = existing.size + 1
        val baseObj = objectives[step]
        val redoPrompt = "Provide an alternative explanation and fresh pedagogical perspective for the learning objective: '${baseObj.description}' regarding '${subtopic.name}'. Explain using alternative clinical analogies, different mnemonic frameworks, practical clinical breakdown, and simplified high-yield bullet points to help me master this concept from another point of view."
        
        studyLoading[step] = true
        studyErrors[step] = null
        scope.launch {
            try {
                val notes = studentViewModel.repositoryChat(userId, redoPrompt)
                if (notes.isNotBlank() && !notes.contains("consultation failed", ignoreCase = true) && !notes.contains("unable to contact", ignoreCase = true) && !notes.contains("failed to reconnect", ignoreCase = true) && !notes.startsWith("Error", ignoreCase = true)) {
                    studyNotes[step] = notes
                    studentViewModel.updateSubtopicCachedContent(subtopicId, gson.toJson(studyNotes.toMap()))
                    
                    val newVer = ExplanationVersion(
                        versionNumber = nextVer,
                        content = notes,
                        tag = "Alternative Angle #$nextVer"
                    )
                    val updated = PreferenceManager.saveSubtopicExplanationVersion(context, subtopicId, step, newVer)
                    explanationVersions[step] = updated
                    activeVersionIndex[step] = updated.lastIndex
                } else {
                    studyErrors[step] = "Offline: Unable to regenerate alternative explanation. Please verify your connection status and tap Retry."
                }
            } catch (e: Exception) {
                studyErrors[step] = "Offline: Unable to regenerate alternative explanation. Please verify your connection status and tap Retry."
            } finally {
                studyLoading[step] = false
            }
        }
    }

    // Check existing bookmarks
    val localBookmarks by studentViewModel.bookmarks.collectAsState(initial = emptyList())
    LaunchedEffect(localBookmarks, subtopicId) {
        isBookmarked = localBookmarks.any { it.target == subtopicId.toString() && it.type == "learn" }
    }

    // Load cached study content from local database instantly on launch (offline-first support)
    LaunchedEffect(subtopic) {
        val cachedJson = subtopic.cachedContentJson
        if (!cachedJson.isNullOrBlank()) {
            try {
                val mapType = object : com.google.gson.reflect.TypeToken<Map<Int, String>>() {}.type
                val map = gson.fromJson<Map<Int, String>>(cachedJson, mapType)
                map?.forEach { (k, v) ->
                    if (v != null && !v.contains("consultation failed", ignoreCase = true) && !v.contains("unable to contact", ignoreCase = true) && !v.contains("failed to reconnect", ignoreCase = true)) {
                        studyNotes[k] = v
                        refreshVersionsForStep(k, v)
                    }
                }
            } catch (e: Exception) {
                // Handle or ignore JSON errors
            }
        }
    }

    LaunchedEffect(currentStep, subtopicId) {
        refreshVersionsForStep(currentStep)
    }

    // Auto-fetch study content from AI when stepping onto an objective (if not cached locally)
    LaunchedEffect(isStudyingStarted, currentStep) {
        if (isStudyingStarted && studyNotes[currentStep] == null && studyLoading[currentStep] != true) {
            studyLoading[currentStep] = true
            studyErrors[currentStep] = null
            scope.launch {
                try {
                    val prompt = objectives[currentStep].prompt
                    val notes = studentViewModel.repositoryChat(userId, prompt)
                    if (notes.isNotBlank() && !notes.contains("consultation failed", ignoreCase = true) && !notes.contains("unable to contact", ignoreCase = true) && !notes.contains("failed to reconnect", ignoreCase = true) && !notes.startsWith("Error", ignoreCase = true)) {
                        studyNotes[currentStep] = notes
                        // Instantly cache the notes in local Room SQLite Database (guarantees offline availability)
                        studentViewModel.updateSubtopicCachedContent(subtopicId, gson.toJson(studyNotes.toMap()))
                        refreshVersionsForStep(currentStep, notes)
                    } else {
                        // DO NOT write the fail as learnt content!
                        studyErrors[currentStep] = "Offline: Unable to download notes for this objective. Please verify your connection status and tap Retry."
                    }
                } catch (e: Exception) {
                    studyErrors[currentStep] = "Offline: Unable to download notes for this objective. Please verify your connection status and tap Retry."
                } finally {
                    studyLoading[currentStep] = false
                }
            }
        }
    }

    val scrollState = rememberScrollState()

    Box(modifier = Modifier.fillMaxSize()) {
        DynamicBackground()

        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                Column {
                    TopAppBar(
                        title = {
                            Column {
                                Text(subtopic.name, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, maxLines = 1)
                                Text(targetUnitName, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                            }
                        },
                        navigationIcon = {
                            IconButton(onClick = {
                                com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                onBack()
                            }) {
                                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                            }
                        },
                        actions = {
                            if (isStudyingStarted) {
                                IconButton(onClick = {
                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                    isHighlighterBarOpen = !isHighlighterBarOpen
                                }) {
                                    BadgedBox(badge = {
                                        if (subtopicHighlights.isNotEmpty()) {
                                            Badge(containerColor = MaterialTheme.colorScheme.primary) {
                                                Text("${subtopicHighlights.size}", fontSize = 9.sp)
                                            }
                                        }
                                    }) {
                                        Icon(
                                            imageVector = Icons.Default.BorderColor,
                                            contentDescription = "Text Highlighter",
                                            tint = if (isHighlighterBarOpen) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                        )
                                    }
                                }

                                IconButton(onClick = {
                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                    if (isBookmarked) {
                                        scope.launch {
                                            val bm = localBookmarks.find { it.target == subtopicId.toString() && it.type == "learn" }
                                            if (bm != null) {
                                                studentViewModel.deleteBookmark(bm.id)
                                            }
                                        }
                                    } else {
                                        showBookmarkDialog = true
                                    }
                                }) {
                                    Icon(
                                        imageVector = if (isBookmarked) Icons.Default.Bookmark else Icons.Default.BookmarkBorder,
                                        contentDescription = "Bookmark",
                                        tint = if (isBookmarked) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                    )
                                }
                            }
                        },
                        colors = TopAppBarDefaults.topAppBarColors(
                            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.6f)
                        )
                    )

                    AnimatedVisibility(visible = isStudyingStarted && isHighlighterBarOpen) {
                        HighlighterBar(
                            selectedColor = selectedHighlightColor,
                            onColorSelected = { selectedHighlightColor = it },
                            highlightsCount = subtopicHighlights.size,
                            onAddHighlightClick = { showAddHighlightDialog = true },
                            onManageHighlightsClick = { showManageHighlightsDialog = true },
                            onCloseClick = { isHighlighterBarOpen = false }
                        )
                    }
                }
            }
        ) { padding ->
            androidx.compose.animation.Crossfade(
                targetState = isStudyingStarted,
                modifier = Modifier.padding(padding),
                label = "StudyScreenFade"
            ) { activeStudy ->
                if (!activeStudy) {
                    // STEP 1: Academic Objectives Overview Screen (Exact Subunit Learning Objectives)
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(20.dp)
                            .verticalScroll(rememberScrollState()),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Surface(
                            shape = MaterialTheme.shapes.extraLarge,
                            color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                            modifier = Modifier.size(72.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Default.MenuBook,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(36.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(24.dp))
                        Text(
                            text = "Academic Objectives Overview",
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Black,
                            color = MaterialTheme.colorScheme.primary,
                            textAlign = TextAlign.Center
                        )
                        Text(
                            text = "Before you begin, review the precise sub-unit learning objectives mapped for this syllabus node.",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.outline,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.padding(top = 8.dp, bottom = 24.dp)
                        )

                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.2f))
                        ) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                                objectives.forEachIndexed { i, obj ->
                                    Row(verticalAlignment = Alignment.Top) {
                                        Surface(
                                            shape = androidx.compose.foundation.shape.CircleShape,
                                            color = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                                            modifier = Modifier.size(24.dp)
                                        ) {
                                            Box(contentAlignment = Alignment.Center) {
                                                Text("${i + 1}", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                                            }
                                        }
                                        Spacer(modifier = Modifier.width(12.dp))
                                        Column {
                                            Text(obj.title, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                                            Text(obj.description, fontSize = 11.sp, color = MaterialTheme.colorScheme.outline)
                                        }
                                    }
                                }
                            }
                        }

                        if (subtopic.isCompleted || studyNotes.isNotEmpty()) {
                            Surface(
                                color = Color(0xFF10B981).copy(alpha = 0.15f),
                                shape = RoundedCornerShape(12.dp),
                                border = BorderStroke(1.dp, Color(0xFF10B981).copy(alpha = 0.4f)),
                                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(12.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(22.dp))
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text("Covered Subtopic", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                                        Text("You've already explored this area. You can review saved notes or redo any part with alternative explanations.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(20.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(10.dp)
                        ) {
                            Button(
                                onClick = {
                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                    isStudyingStarted = true
                                },
                                shape = MaterialTheme.shapes.large,
                                modifier = Modifier.weight(1f).height(52.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                            ) {
                                Text(if (subtopic.isCompleted || studyNotes.isNotEmpty()) "REVIEW NOTES 📖" else "PROCEED TO STUDY 🚀", fontWeight = FontWeight.Bold)
                            }

                            if (subtopic.isCompleted || studyNotes.isNotEmpty()) {
                                OutlinedButton(
                                    onClick = {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        isStudyingStarted = true
                                        redoExplanationForStep(0)
                                    },
                                    shape = MaterialTheme.shapes.large,
                                    modifier = Modifier.weight(1f).height(52.dp)
                                ) {
                                    Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(16.dp))
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("REDO & REGEN 🔄", fontWeight = FontWeight.Bold, fontSize = 11.sp)
                                }
                            }
                        }
                    }
                } else {
                    // STEP 2: Interactive sliding interface prompting AI on demand
                    val isCurrentLoading = studyLoading[currentStep] == true
                    val currentContent = studyNotes[currentStep]
                    val currentError = studyErrors[currentStep]

                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 16.dp)
                    ) {
                        // Topic objective slide
                        Card(
                            modifier = Modifier
                                .weight(1f)
                                .fillMaxWidth()
                                .verticalScroll(scrollState),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
                            ),
                            shape = MaterialTheme.shapes.large
                        ) {
                            Column(modifier = Modifier.padding(18.dp)) {
                                Text(
                                    text = objectives[currentStep].title,
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    text = objectives[currentStep].description,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.outline,
                                    modifier = Modifier.padding(bottom = 12.dp)
                                )

                                // Explanation Versions & Redo Header Controls at Top
                                val currentStepVersions = explanationVersions[currentStep] ?: emptyList()
                                val currentActiveVerIndex = activeVersionIndex[currentStep] ?: 0

                                Surface(
                                    shape = RoundedCornerShape(12.dp),
                                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f)),
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(bottom = 14.dp)
                                ) {
                                    Column(modifier = Modifier.padding(10.dp)) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                if (subtopic.isCompleted || studyNotes[currentStep] != null) {
                                                    Surface(
                                                        color = Color(0xFF10B981).copy(alpha = 0.2f),
                                                        shape = RoundedCornerShape(6.dp),
                                                        modifier = Modifier.padding(end = 6.dp)
                                                    ) {
                                                        Text(
                                                            text = if (subtopic.isCompleted) "COVERED ✓" else "SAVED",
                                                            fontSize = 9.sp,
                                                            fontWeight = FontWeight.Black,
                                                            color = Color(0xFF047857),
                                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                                        )
                                                    }
                                                }
                                                Icon(
                                                    imageVector = Icons.Default.AutoAwesome,
                                                    contentDescription = null,
                                                    tint = MaterialTheme.colorScheme.primary,
                                                    modifier = Modifier.size(14.dp)
                                                )
                                                Spacer(modifier = Modifier.width(4.dp))
                                                Text(
                                                    text = if (currentStepVersions.size > 1) {
                                                        "Explanation ${currentActiveVerIndex + 1} of ${currentStepVersions.size}"
                                                    } else {
                                                        "Active Explanation"
                                                    },
                                                    fontSize = 11.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    color = MaterialTheme.colorScheme.onSurface
                                                )
                                            }

                                            // Small option at the top for viewing older ones
                                            if (currentStepVersions.size > 1) {
                                                TextButton(
                                                    onClick = {
                                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                                        showOlderVersionsDialog = true
                                                    },
                                                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                                                    modifier = Modifier.height(28.dp)
                                                ) {
                                                    Icon(
                                                        imageVector = Icons.Default.History,
                                                        contentDescription = null,
                                                        modifier = Modifier.size(13.dp),
                                                        tint = MaterialTheme.colorScheme.primary
                                                    )
                                                    Spacer(modifier = Modifier.width(4.dp))
                                                    Text(
                                                        "Older Versions (${currentStepVersions.size})",
                                                        fontSize = 11.sp,
                                                        fontWeight = FontWeight.SemiBold,
                                                        color = MaterialTheme.colorScheme.primary
                                                    )
                                                }
                                            }
                                        }

                                        Spacer(modifier = Modifier.height(6.dp))

                                        // Quick Version Chips & Regenerate / Redo button
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            if (currentStepVersions.isNotEmpty()) {
                                                LazyRow(
                                                    modifier = Modifier.weight(1f, fill = false),
                                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                                ) {
                                                    itemsIndexed(currentStepVersions) { vIdx, ver ->
                                                        val isSelected = vIdx == currentActiveVerIndex
                                                        FilterChip(
                                                            selected = isSelected,
                                                            onClick = {
                                                                com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                                                activeVersionIndex[currentStep] = vIdx
                                                                studyNotes[currentStep] = ver.content
                                                            },
                                                            label = {
                                                                Text(
                                                                    text = if (vIdx == 0) "v1 (Original)" else "v${vIdx + 1} (Alternative)",
                                                                    fontSize = 10.sp,
                                                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                                                                )
                                                            },
                                                            leadingIcon = if (isSelected) {
                                                                {
                                                                    Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(11.dp))
                                                                }
                                                            } else null,
                                                            colors = FilterChipDefaults.filterChipColors(
                                                                selectedContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                                                                selectedLabelColor = MaterialTheme.colorScheme.primary
                                                            ),
                                                            shape = RoundedCornerShape(8.dp),
                                                            modifier = Modifier.height(28.dp)
                                                        )
                                                    }
                                                }
                                            } else {
                                                Text(
                                                    text = "Alternative explanations can be regenerated",
                                                    fontSize = 10.sp,
                                                    color = MaterialTheme.colorScheme.outline
                                                )
                                            }

                                            Spacer(modifier = Modifier.width(8.dp))

                                            // Regenerate / Redo button (inside each covered subtopic)
                                            FilledTonalButton(
                                                onClick = {
                                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                                    redoExplanationForStep(currentStep)
                                                },
                                                enabled = !isCurrentLoading,
                                                shape = RoundedCornerShape(8.dp),
                                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp),
                                                modifier = Modifier.height(28.dp)
                                            ) {
                                                Icon(
                                                    imageVector = Icons.Default.Refresh,
                                                    contentDescription = "Regenerate",
                                                    modifier = Modifier.size(13.dp)
                                                )
                                                Spacer(modifier = Modifier.width(4.dp))
                                                Text(
                                                    text = if (currentStepVersions.isNotEmpty()) "Redo / Alternative" else "Regenerate",
                                                    fontSize = 11.sp,
                                                    fontWeight = FontWeight.Bold
                                                )
                                            }
                                        }
                                    }
                                }
                                
                                if (isCurrentLoading) {
                                    Box(
                                        modifier = Modifier.fillMaxWidth().padding(vertical = 48.dp),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                                            Spacer(modifier = Modifier.height(16.dp))
                                            Text("Socratic AI is formulating core notes...", fontSize = 12.sp, color = MaterialTheme.colorScheme.outline)
                                        }
                                    }
                                } else if (currentError != null) {
                                    Column(
                                        modifier = Modifier.fillMaxWidth().padding(vertical = 32.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        Text(currentError, color = MaterialTheme.colorScheme.error, fontSize = 13.sp, textAlign = TextAlign.Center)
                                        Spacer(modifier = Modifier.height(12.dp))
                                        Button(onClick = {
                                            studyLoading[currentStep] = true
                                            studyErrors[currentStep] = null
                                            scope.launch {
                                                try {
                                                    val res = studentViewModel.repositoryChat(userId, objectives[currentStep].prompt)
                                                    if (res.isNotBlank() && !res.contains("consultation failed", ignoreCase = true) && !res.contains("unable to contact", ignoreCase = true) && !res.contains("failed to reconnect", ignoreCase = true) && !res.startsWith("Error", ignoreCase = true)) {
                                                        studyNotes[currentStep] = res
                                                        studentViewModel.updateSubtopicCachedContent(subtopicId, gson.toJson(studyNotes.toMap()))
                                                    } else {
                                                        studyErrors[currentStep] = "Offline: Unable to reconnect to Socratic Engine. Please verify your connection status and tap Retry."
                                                    }
                                                } catch (e: Exception) {
                                                    studyErrors[currentStep] = "Offline: Unable to reconnect to Socratic Engine. Please verify your connection status and tap Retry."
                                                } finally {
                                                    studyLoading[currentStep] = false
                                                }
                                            }
                                        }) {
                                            Text("Retry Connection")
                                        }
                                    }
                                } else {
                                    FormattedText(
                                        text = currentContent ?: "",
                                        highlights = subtopicHighlights,
                                        onLinkClicked = { link ->
                                            onNavigateToBrowser(link)
                                        }
                                    )

                                    Spacer(modifier = Modifier.height(16.dp))
                                    Text(
                                        text = "High-Yield Video & Web References",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    com.example.edu_ai.ui.components.VideoRecommendationCard(
                                        title = "Video Lecture & Clinical Breakdown: ${subtopic.name}",
                                        url = "https://www.youtube.com/results?search_query=" + java.net.URLEncoder.encode(subtopic.name + " clinical lecture osmosis ninja nerd", "UTF-8"),
                                        onOpen = {
                                            onNavigateToBrowser("https://www.youtube.com/results?search_query=" + java.net.URLEncoder.encode(subtopic.name + " clinical lecture osmosis ninja nerd", "UTF-8"))
                                        }
                                    )
                                    Spacer(modifier = Modifier.height(6.dp))
                                    com.example.edu_ai.ui.components.WebReferenceCard(
                                        title = "PubMed Evidence & Research: ${subtopic.name}",
                                        url = "https://pubmed.ncbi.nlm.nih.gov/?term=" + java.net.URLEncoder.encode(subtopic.name, "UTF-8"),
                                        onOpen = {
                                            onNavigateToBrowser("https://pubmed.ncbi.nlm.nih.gov/?term=" + java.net.URLEncoder.encode(subtopic.name, "UTF-8"))
                                        }
                                    )
                                }

                                Spacer(modifier = Modifier.height(20.dp))

                                // AI Consultation window
                                if (inquiries.isNotEmpty() || isAiLoading) {
                                    Card(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(vertical = 10.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.3f)
                                        )
                                    ) {
                                        Column(modifier = Modifier.padding(12.dp)) {
                                            Row(
                                                verticalAlignment = Alignment.CenterVertically,
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                modifier = Modifier.fillMaxWidth()
                                            ) {
                                                Row(verticalAlignment = Alignment.CenterVertically) {
                                                    Icon(
                                                        Icons.Default.Star,
                                                        contentDescription = null,
                                                        tint = MaterialTheme.colorScheme.primary,
                                                        modifier = Modifier.size(16.dp)
                                                    )
                                                    Spacer(modifier = Modifier.width(6.dp))
                                                    Text(
                                                        "Interactive AI Consultations",
                                                        style = MaterialTheme.typography.labelMedium,
                                                        fontWeight = FontWeight.Bold,
                                                        color = MaterialTheme.colorScheme.primary
                                                    )
                                                }
                                                if (inquiries.isNotEmpty()) {
                                                    IconButton(
                                                        onClick = {
                                                            inquiries.clear()
                                                            com.example.edu_ai.utils.PreferenceManager.saveSubtopicInquiries(context, subtopicId, "[]")
                                                        },
                                                        modifier = Modifier.size(24.dp)
                                                    ) {
                                                        Icon(
                                                            Icons.Default.Delete,
                                                            contentDescription = "Clear History",
                                                            tint = MaterialTheme.colorScheme.error.copy(alpha = 0.6f),
                                                            modifier = Modifier.size(14.dp)
                                                        )
                                                    }
                                                }
                                            }
                                            Spacer(modifier = Modifier.height(8.dp))
                                            
                                            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                                inquiries.forEach { inquiry ->
                                                    Column(
                                                        modifier = Modifier
                                                            .fillMaxWidth()
                                                            .background(
                                                                MaterialTheme.colorScheme.surface.copy(alpha = 0.5f),
                                                                RoundedCornerShape(8.dp)
                                                            )
                                                            .padding(8.dp)
                                                    ) {
                                                        Text(
                                                            text = "Q: " + inquiry.question,
                                                            fontWeight = FontWeight.Bold,
                                                            fontSize = 11.sp,
                                                            color = MaterialTheme.colorScheme.primary,
                                                            modifier = Modifier.padding(bottom = 4.dp)
                                                        )
                                                        if (inquiry.answer.isEmpty()) {
                                                            Box(
                                                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                                                contentAlignment = Alignment.CenterStart
                                                            ) {
                                                                CircularProgressIndicator(modifier = Modifier.size(16.dp))
                                                            }
                                                        } else {
                                                            FormattedText(
                                                                text = inquiry.answer,
                                                                highlights = subtopicHighlights,
                                                                style = MaterialTheme.typography.bodySmall.copy(fontSize = 12.sp)
                                                            )
                                                        }
                                                    }
                                                }
                                                
                                                if (isAiLoading && (inquiries.isEmpty() || inquiries.last().answer.isNotEmpty())) {
                                                    Box(
                                                        modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                                                        contentAlignment = Alignment.Center
                                                    ) {
                                                        CircularProgressIndicator(modifier = Modifier.size(20.dp))
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Bottom Socratic Inquiry box
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                            )
                        ) {
                            Column(modifier = Modifier.padding(10.dp)) {
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(bottom = 6.dp)
                                ) {
                                    StudyChip("Foundations to Mastery") {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        val q = "Explain '${subtopic.name}' step-by-step: start with foundational concepts and basic definitions, work through intermediate mechanisms, and culminate in major concepts and clinical takeaways."
                                        aiQuestion = ""
                                        val tempItem = InquiryItem(q, "")
                                        inquiries.add(tempItem)
                                        isAiLoading = true
                                        val promptWithInstructions = q + " (Educational instruction: Make clear, well-structured notes. Do not view, adapt to, or assume any student status. Be strictly objective and conclusive. Start with foundational concepts and core definitions first, then work up to intermediate mechanisms and major concepts with definitive takeaways.)"
                                        triggerAiConsultation(userId, promptWithInstructions, studentViewModel, scope) { loading, res ->
                                            isAiLoading = loading
                                            if (!loading) {
                                                val idx = inquiries.indexOf(tempItem)
                                                if (idx != -1) {
                                                    inquiries[idx] = tempItem.copy(answer = res ?: "No response received.")
                                                } else {
                                                    inquiries.add(InquiryItem(q, res ?: "No response received."))
                                                }
                                                val json = gson.toJson(inquiries.toList())
                                                com.example.edu_ai.utils.PreferenceManager.saveSubtopicInquiries(context, subtopicId, json)
                                            }
                                        }
                                    }
                                    StudyChip("Explain with analogy") {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        val q = "Please explain the foundational concepts and mechanisms of '${subtopic.name}' using a simple, relatable analogy, then bridge it to major clinical concepts."
                                        aiQuestion = ""
                                        val tempItem = InquiryItem(q, "")
                                        inquiries.add(tempItem)
                                        isAiLoading = true
                                        val promptWithInstructions = q + " (Educational instruction: Make clear, objective, and conclusive notes. Do not view or assume any student status. Start with foundational concepts using a relatable analogy, then bridge to major concepts and definitive clinical takeaways.)"
                                        triggerAiConsultation(userId, promptWithInstructions, studentViewModel, scope) { loading, res ->
                                            isAiLoading = loading
                                            if (!loading) {
                                                val idx = inquiries.indexOf(tempItem)
                                                if (idx != -1) {
                                                    inquiries[idx] = tempItem.copy(answer = res ?: "No response received.")
                                                } else {
                                                    inquiries.add(InquiryItem(q, res ?: "No response received."))
                                                }
                                                val json = gson.toJson(inquiries.toList())
                                                com.example.edu_ai.utils.PreferenceManager.saveSubtopicInquiries(context, subtopicId, json)
                                            }
                                        }
                                    }
                                    StudyChip("Exam pearls") {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        val q = "What are the core fundamentals and high-yield board exam pearls regarding '${subtopic.name}'?"
                                        aiQuestion = ""
                                        val tempItem = InquiryItem(q, "")
                                        inquiries.add(tempItem)
                                        isAiLoading = true
                                        val promptWithInstructions = q + " (Educational instruction: Make clear, objective, and conclusive notes without viewing student status. Start with foundational principles before detailing high-yield traps and major clinical pearls with definitive conclusions.)"
                                        triggerAiConsultation(userId, promptWithInstructions, studentViewModel, scope) { loading, res ->
                                            isAiLoading = loading
                                            if (!loading) {
                                                val idx = inquiries.indexOf(tempItem)
                                                if (idx != -1) {
                                                    inquiries[idx] = tempItem.copy(answer = res ?: "No response received.")
                                                } else {
                                                    inquiries.add(InquiryItem(q, res ?: "No response received."))
                                                }
                                                val json = gson.toJson(inquiries.toList())
                                                com.example.edu_ai.utils.PreferenceManager.saveSubtopicInquiries(context, subtopicId, json)
                                            }
                                        }
                                    }
                                }

                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    OutlinedTextField(
                                        value = aiQuestion,
                                        onValueChange = { aiQuestion = it },
                                        placeholder = { Text("Ask about ${subtopic.name}...", fontSize = 11.sp) },
                                        modifier = Modifier.weight(1f),
                                        textStyle = MaterialTheme.typography.bodyMedium.copy(fontSize = 12.sp),
                                        maxLines = 2,
                                        colors = OutlinedTextFieldDefaults.colors(
                                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                                            unfocusedBorderColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.2f)
                                        )
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    IconButton(
                                        onClick = {
                                            com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                            val q = aiQuestion.trim()
                                            if (q.isNotEmpty()) {
                                                aiQuestion = ""
                                                val tempItem = InquiryItem(q, "")
                                                inquiries.add(tempItem)
                                                isAiLoading = true
                                                val promptWithInstructions = q + " (Educational instruction: Make clear, objective, and conclusive notes. Do not view or assume any student status. Always start with foundational concepts and core definitions, then work up to major concepts with definitive conclusions.)"
                                                triggerAiConsultation(userId, promptWithInstructions, studentViewModel, scope) { loading, res ->
                                                    isAiLoading = loading
                                                    if (!loading) {
                                                        val idx = inquiries.indexOf(tempItem)
                                                        if (idx != -1) {
                                                            inquiries[idx] = tempItem.copy(answer = res ?: "No response received.")
                                                        } else {
                                                            inquiries.add(InquiryItem(q, res ?: "No response received."))
                                                        }
                                                        val json = gson.toJson(inquiries.toList())
                                                        com.example.edu_ai.utils.PreferenceManager.saveSubtopicInquiries(context, subtopicId, json)
                                                    }
                                                }
                                            }
                                        },
                                        enabled = !isAiLoading
                                    ) {
                                        Icon(
                                            Icons.Default.Send,
                                            contentDescription = "Send",
                                            tint = MaterialTheme.colorScheme.primary
                                        )
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Previous/Next controllers
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Button(
                                onClick = {
                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                    if (currentStep > 0) currentStep--
                                },
                                enabled = currentStep > 0,
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                            ) {
                                Text("PREVIOUS", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }

                            if (currentStep == objectives.lastIndex) {
                                Button(
                                    onClick = {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        scope.launch {
                                            studentViewModel.toggleSubtopicCompleted(userId, subtopicId, true)
                                        }
                                        showQuizPromptDialog = true
                                    },
                                    enabled = !isCurrentLoading,
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                                ) {
                                    Icon(Icons.Default.CheckCircle, contentDescription = null, modifier = Modifier.size(16.dp))
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("COMPLETE & SYNC", fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }
                            } else {
                                Button(
                                    onClick = {
                                        com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                        if (currentStep < objectives.lastIndex) currentStep++
                                    },
                                    enabled = !isCurrentLoading,
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                                ) {
                                    Text("NEXT PART", fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Bookmark Note Input Dialog
    if (showBookmarkDialog) {
        AlertDialog(
            onDismissRequest = { showBookmarkDialog = false },
            title = { Text("Save Bookmark Clip") },
            text = {
                Column {
                    Text("Add custom clinical notes or quick reminders to this clip.", fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(10.dp))
                    OutlinedTextField(
                        value = bookmarkNote,
                        onValueChange = { bookmarkNote = it },
                        placeholder = { Text("E.g., high-yield topic for cardiac pathology exam...") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    scope.launch {
                        studentViewModel.addBookmark(
                            userId = userId,
                            type = "learn",
                            title = subtopic.name,
                            target = subtopicId.toString(),
                            context = (studyNotes[currentStep] ?: "").take(160) + "...",
                            notes = bookmarkNote.trim().ifEmpty { null }
                        )
                        isBookmarked = true
                        showBookmarkDialog = false
                        bookmarkNote = ""
                    }
                }) {
                    Text("Save Clip")
                }
            },
            dismissButton = {
                TextButton(onClick = { showBookmarkDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }

    // Subtopic Completion Quiz Prompt Dialog
    if (showQuizPromptDialog) {
        val subtopicName = subtopic.name
        val unitNameForQuiz = if (targetUnitName.isNotEmpty() && targetUnitName != "Clinical Science") {
            targetUnitName
        } else {
            dbSubtopicUnitName ?: targetUnitName
        }

        AlertDialog(
            onDismissRequest = {
                showQuizPromptDialog = false
                onBack()
            },
            icon = {
                Icon(
                    imageVector = Icons.Default.Psychology,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(36.dp)
                )
            },
            title = {
                Text(
                    text = "Subtopic Completed!",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    textAlign = TextAlign.Center
                )
            },
            text = {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = "You've successfully completed all learning objectives for:",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.45f),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                    ) {
                        Text(
                            text = subtopicName,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            textAlign = TextAlign.Center
                        )
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Would you like to take the knowledge retrieval quiz on this subtopic now, or skip for now?",
                        fontSize = 12.sp,
                        lineHeight = 17.sp,
                        textAlign = TextAlign.Center,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        showQuizPromptDialog = false
                        onNavigateToQuiz(unitNameForQuiz, subtopicName)
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Icon(Icons.Default.School, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Take Quiz", fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                OutlinedButton(
                    onClick = {
                        showQuizPromptDialog = false
                        onBack()
                    },
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("Skip")
                }
            }
        )
    }

    // Quick Add Highlight Dialog
    if (showAddHighlightDialog) {
        QuickAddHighlightDialog(
            selectedColor = selectedHighlightColor,
            onDismiss = { showAddHighlightDialog = false },
            onConfirm = { text, color, note ->
                val newHl = TextHighlight(
                    text = text,
                    colorHex = color.hex,
                    label = color.displayName,
                    subtopicId = subtopicId,
                    targetKey = "subtopic_$subtopicId",
                    note = note
                )
                subtopicHighlights = HighlightManager.saveHighlight(context, newHl)
                showAddHighlightDialog = false
            }
        )
    }

    // Manage Highlights Bottom Sheet
    if (showManageHighlightsDialog) {
        ManageHighlightsBottomSheet(
            highlights = subtopicHighlights,
            onDeleteHighlight = { id ->
                subtopicHighlights = HighlightManager.removeHighlight(context, subtopicId, id)
            },
            onClearAll = {
                HighlightManager.clearAllHighlights(context, subtopicId)
                subtopicHighlights = emptyList()
                showManageHighlightsDialog = false
            },
            onDismiss = { showManageHighlightsDialog = false }
        )
    }

    // Older Versions Dialog for reviewing alternative explanations
    if (showOlderVersionsDialog) {
        val currentStepVersions = explanationVersions[currentStep] ?: emptyList()
        val currentActiveVerIndex = activeVersionIndex[currentStep] ?: 0
        AlertDialog(
            onDismissRequest = { showOlderVersionsDialog = false },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.History, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Saved Explanation Versions", fontSize = 16.sp, fontWeight = FontWeight.Bold)
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
                        "Select any past explanation to review or switch active view.",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.outline
                    )
                    currentStepVersions.forEachIndexed { vIdx, ver ->
                        val isSelected = vIdx == currentActiveVerIndex
                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = if (isSelected) MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f) else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f),
                            border = BorderStroke(
                                1.dp,
                                if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)
                            ),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    com.example.edu_ai.utils.TactileFeedback.triggerSubtleClick(context)
                                    activeVersionIndex[currentStep] = vIdx
                                    studyNotes[currentStep] = ver.content
                                    showOlderVersionsDialog = false
                                }
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = if (vIdx == 0) "Version 1 (Original)" else "Version ${vIdx + 1} (${ver.tag.ifEmpty { "Alternative" }})",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                    )
                                    if (isSelected) {
                                        Surface(
                                            color = MaterialTheme.colorScheme.primary,
                                            shape = RoundedCornerShape(4.dp)
                                        ) {
                                            Text(
                                                "ACTIVE",
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.Bold,
                                                color = MaterialTheme.colorScheme.onPrimary,
                                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                            )
                                        }
                                    }
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                val dateStr = java.text.SimpleDateFormat("MMM dd, HH:mm", java.util.Locale.getDefault()).format(java.util.Date(ver.timestamp))
                                Text("Generated: $dateStr", fontSize = 10.sp, color = MaterialTheme.colorScheme.outline)
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = ver.content.take(160) + if (ver.content.length > 160) "..." else "",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    lineHeight = 15.sp
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {
                Button(onClick = { showOlderVersionsDialog = false }) {
                    Text("Done")
                }
            }
        )
    }
}

data class SyllabusObjective(val title: String, val description: String, val prompt: String)

data class InquiryItem(val question: String, val answer: String, val timestamp: Long = System.currentTimeMillis())

@Composable
fun StudyChip(text: String, onClick: () -> Unit) {
    SuggestionChip(
        onClick = onClick,
        label = { Text(text, fontSize = 11.sp, fontWeight = FontWeight.Bold) }
    )
}

private fun triggerAiConsultation(
    userId: String,
    aiQuestion: String,
    viewModel: StudentViewModel,
    scope: kotlinx.coroutines.CoroutineScope,
    onResult: (Boolean, String?) -> Unit
) {
    onResult(true, null)
    scope.launch {
        try {
            val response = viewModel.repositoryChat(userId, aiQuestion)
            onResult(false, response)
        } catch (e: Exception) {
            onResult(false, "System was unable to contact modular clinical AI. Please verify your connection status.")
        }
    }
}
