package com.example.edu_ai.ui.screens.student

import androidx.compose.animation.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.edu_ai.data.local.UnitWithModules
import com.example.edu_ai.data.local.UserEntity
import com.example.edu_ai.data.local.exactFieldName
import com.example.edu_ai.data.local.exactCourseName
import com.example.edu_ai.data.local.exactUnitGroupName
import com.example.edu_ai.data.remote.ApiTimetableSlot
import com.example.edu_ai.ui.components.DynamicBackground
import com.example.edu_ai.ui.components.ProgressRings
import com.example.edu_ai.ui.components.RingProgress
import com.example.edu_ai.utils.TactileFeedback
import com.example.edu_ai.utils.PreferenceManager
import com.example.edu_ai.utils.UpdateManager
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StudentDashboard(
    userId: String,
    onLogout: () -> Unit,
    onLaunchModule: () -> Unit,
    onOpenLibrary: () -> Unit,
    onLaunchUnit: (Long) -> Unit,
    onOpenBookmarks: () -> Unit,
    onOpenSettings: () -> Unit = {},
    initialTab: String = "dashboard",
    initialUnit: String? = null,
    initialTopic: String? = null,
    viewModel: StudentViewModel = viewModel(factory = StudentViewModel.Factory)
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    
    val user = uiState.user ?: UserEntity(id = userId, username = "Student", role = "student", sensoryMode = "Visual", semesterStatus = "Year 4 - Medical Candidate", aiPersona = "Socratic Mentor")

    val progressViewModel: ProgressViewModel = viewModel(key = "progress_$userId", factory = ProgressViewModel.provideFactory(user))
    val recommendation by progressViewModel.recommendation.collectAsState()
    val progressUiState by progressViewModel.uiState.collectAsState()
    
    val timetableViewModel: TimetableViewModel = viewModel(key = "timetable_$userId", factory = TimetableViewModel.provideFactory(user))
    val timetableUiState by timetableViewModel.uiState.collectAsState()

    val chatViewModel: ChatViewModel = viewModel(key = "chat_$userId", factory = ChatViewModel.provideFactory(user))
    val quizViewModel: QuizViewModel = viewModel(key = "quiz_$userId", factory = QuizViewModel.provideFactory(user))

    var currentTab by remember { mutableStateOf(if (initialTab.isNotEmpty()) initialTab else "dashboard") }

    LaunchedEffect(userId) {
        viewModel.setUserId(userId)
        viewModel.refreshDashboard(userId)
        progressViewModel.refreshRecommendations()
    }

    LaunchedEffect(initialTab, initialUnit, initialTopic) {
        if (initialTab.isNotEmpty()) {
            currentTab = initialTab
        }
        if (initialTab == "assessment" && !initialUnit.isNullOrBlank()) {
            quizViewModel.startQuiz(initialUnit, initialTopic?.ifBlank { null })
        }
    }
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    var isRightDrawerOpen by remember { mutableStateOf(false) }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet(
                drawerContainerColor = MaterialTheme.colorScheme.surface,
                modifier = Modifier.width(300.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp)
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Surface(
                                shape = MaterialTheme.shapes.medium,
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f),
                                modifier = Modifier.size(36.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Text("T", fontWeight = FontWeight.Black, fontSize = 20.sp, color = MaterialTheme.colorScheme.primary)
                                }
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "Trace Learning",
                                fontWeight = FontWeight.Black,
                                fontSize = 22.sp,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "Student: ${user.username}",
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                        Text(
                            text = "Level: ${user.semesterStatus}",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.outline
                        )
                        Text(
                            text = "Sensory Mode: ${user.sensoryMode}",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))
                Spacer(modifier = Modifier.height(12.dp))

                NavigationDrawerItem(
                    label = { Text("Home Dashboard", fontWeight = FontWeight.Bold) },
                    selected = currentTab == "dashboard",
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        currentTab = "dashboard"
                    },
                    icon = { Icon(Icons.Default.Home, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Socratic Assistant", fontWeight = FontWeight.Bold) },
                    selected = currentTab == "socratic",
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        currentTab = "socratic"
                    },
                    icon = { Icon(Icons.Default.Psychology, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Assessment Center", fontWeight = FontWeight.Bold) },
                    selected = currentTab == "assessment",
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        currentTab = "assessment"
                    },
                    icon = { Icon(Icons.Default.School, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Study Connect & Peers", fontWeight = FontWeight.Bold) },
                    selected = currentTab == "connect",
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        currentTab = "connect"
                    },
                    icon = { Icon(Icons.Default.Group, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Dynamic Schedule", fontWeight = FontWeight.Bold) },
                    selected = currentTab == "timetable",
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        currentTab = "timetable"
                    },
                    icon = { Icon(Icons.Default.DateRange, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Syllabus Library", fontWeight = FontWeight.Bold) },
                    selected = false,
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        onOpenLibrary()
                    },
                    icon = { Icon(Icons.Default.LibraryAdd, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Saved Highlights", fontWeight = FontWeight.Bold) },
                    selected = false,
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        onOpenBookmarks()
                    },
                    icon = { Icon(Icons.Default.Bookmark, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                NavigationDrawerItem(
                    label = { Text("Settings & Version", fontWeight = FontWeight.Bold) },
                    selected = false,
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        onOpenSettings()
                    },
                    icon = { Icon(Icons.Default.Settings, contentDescription = null) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )

                Spacer(modifier = Modifier.weight(1f))

                NavigationDrawerItem(
                    label = { Text("Sign Out", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold) },
                    selected = false,
                    onClick = {
                        scope.launch { drawerState.close() }
                        TactileFeedback.triggerSubtleClick(context)
                        onLogout()
                    },
                    icon = { Icon(Icons.Default.ExitToApp, contentDescription = null, tint = MaterialTheme.colorScheme.error) },
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 0.dp)
                )
            }
        }
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    detectHorizontalDragGestures { change, dragAmount ->
                        change.consume()
                        if (dragAmount < -18) { // Swiping Left -> Opens Loaded Units panel
                            isRightDrawerOpen = true
                        } else if (dragAmount > 18) { // Swiping Right -> Closes Loaded Units panel
                            isRightDrawerOpen = false
                        }
                    }
                }
        ) {
            DynamicBackground()

            Scaffold(
                containerColor = Color.Transparent,
                topBar = {
                    TopAppBar(
                        title = {
                            Column {
                                Text("Trace Learning", fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
                                Text(
                                    text = when (currentTab) {
                                        "socratic" -> "Socratic Clinical Assistant"
                                        "assessment" -> "Knowledge Retrieval Center"
                                        "connect" -> "Peer Network & Chats"
                                        "timetable" -> "Personalized Study Schedule"
                                        else -> "Student Command Center"
                                    },
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.primary
                                )
                            }
                        },
                        navigationIcon = {
                            IconButton(onClick = { scope.launch { drawerState.open() } }) {
                                Icon(Icons.Default.Menu, contentDescription = "Open Drawer")
                            }
                        },
                        actions = {
                            if (currentTab == "dashboard") {
                                IconButton(onClick = onOpenBookmarks) {
                                    Icon(Icons.Default.Bookmark, contentDescription = "Saved Bookmarks", tint = MaterialTheme.colorScheme.primary)
                                }
                            }
                            IconButton(onClick = onOpenSettings) {
                                Icon(Icons.Default.Settings, contentDescription = "Settings & Updates", tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        },
                        colors = TopAppBarDefaults.topAppBarColors(
                            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f)
                        )
                    )
                }
            ) { paddingValues ->
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues)
                ) {
                    when (currentTab) {
                        "dashboard" -> {
                            StudentDashboardContent(
                                user = user,
                                uiState = uiState,
                                recommendation = recommendation,
                                timetableUiState = timetableUiState,
                                quizHistory = progressUiState.quizHistory,
                                onNavigateToTab = { tabName ->
                                    TactileFeedback.triggerSubtleClick(context)
                                    currentTab = tabName
                                },
                                onOpenLibrary = onOpenLibrary,
                                onLaunchUnit = onLaunchUnit,
                                onLaunchModule = onLaunchModule
                            )
                        }
                        "socratic" -> {
                            ChatInterface(
                                viewModel = chatViewModel,
                                onCloseChat = { currentTab = "dashboard" }
                            )
                        }
                        "assessment" -> {
                            QuizTabWrapper(
                                user = user,
                                units = uiState.units,
                                viewModel = quizViewModel
                            )
                        }
                        "connect" -> {
                            ConnectScreen(
                                user = user,
                                viewModel = viewModel,
                                onNavigateToLearn = { subtopicId ->
                                    val firstUnitId = uiState.unitsWithModules.firstOrNull()?.unit?.localId ?: 1L
                                    onLaunchUnit(firstUnitId)
                                }
                            )
                        }
                        "timetable" -> {
                            TimetableTab(viewModel = timetableViewModel)
                        }
                    }
                }
            }

            // Right Drawer Panel (Loaded Units overlay on Swipe Left)
            if (isRightDrawerOpen) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.45f))
                        .clickable { isRightDrawerOpen = false }
                        .zIndex(9f)
                )
            }

            AnimatedVisibility(
                visible = isRightDrawerOpen,
                enter = slideInHorizontally(initialOffsetX = { it }),
                exit = slideOutHorizontally(targetOffsetX = { it }),
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .fillMaxHeight()
                    .width(300.dp)
                    .zIndex(10f)
            ) {
                Surface(
                    color = MaterialTheme.colorScheme.surface.copy(alpha = 0.98f),
                    tonalElevation = 8.dp,
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.2f))
                ) {
                    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = "Loaded Units",
                                fontWeight = FontWeight.Black,
                                fontSize = 18.sp,
                                color = MaterialTheme.colorScheme.primary
                            )
                            IconButton(onClick = { isRightDrawerOpen = false }) {
                                Icon(Icons.Default.Close, contentDescription = "Close")
                            }
                        }
                        Text(
                            text = "Quickly switch syllabus outline context below:",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.outline,
                            modifier = Modifier.padding(bottom = 14.dp)
                        )
                        
                        if (uiState.unitsWithModules.isEmpty()) {
                            Box(modifier = Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                                Text("No units loaded yet.", fontSize = 12.sp, color = MaterialTheme.colorScheme.outline)
                            }
                        } else {
                            LazyColumn(
                                modifier = Modifier.weight(1f),
                                verticalArrangement = Arrangement.spacedBy(10.dp)
                            ) {
                                items(uiState.unitsWithModules) { unitWithModules ->
                                    val unit = unitWithModules.unit
                                    Card(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clickable {
                                                isRightDrawerOpen = false
                                                onLaunchUnit(unit.localId)
                                            },
                                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                                        shape = RoundedCornerShape(12.dp)
                                    ) {
                                        Column(modifier = Modifier.padding(12.dp)) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Surface(
                                                    shape = RoundedCornerShape(4.dp),
                                                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                                                ) {
                                                    Text(
                                                        text = unit.exactFieldName.uppercase(),
                                                        fontSize = 7.sp,
                                                        fontWeight = FontWeight.Black,
                                                        color = MaterialTheme.colorScheme.primary,
                                                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                                    )
                                                }
                                                Spacer(modifier = Modifier.width(4.dp))
                                                Text(
                                                    text = unit.exactCourseName,
                                                    fontSize = 8.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    color = MaterialTheme.colorScheme.secondary
                                                )
                                            }
                                            Spacer(modifier = Modifier.height(2.dp))
                                            Text(unit.unitName, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                                            Text(
                                                text = "${unitWithModules.modules.size} Modules loaded",
                                                fontSize = 10.sp,
                                                color = MaterialTheme.colorScheme.primary
                                            )
                                        }
                                    }
                                }
                            }
                        }
                        
                        Button(
                            onClick = {
                                isRightDrawerOpen = false
                                onOpenLibrary()
                            },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("ADD NEW UNIT")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun StudentDashboardContent(
    user: UserEntity,
    uiState: StudentUiState,
    recommendation: String,
    timetableUiState: TimetableUiState,
    quizHistory: List<com.example.edu_ai.data.local.QuizHistoryEntity>,
    onNavigateToTab: (String) -> Unit,
    onOpenLibrary: () -> Unit,
    onLaunchUnit: (Long) -> Unit,
    onLaunchModule: () -> Unit
) {
    val context = LocalContext.current
    val currentDay = remember {
        SimpleDateFormat("EEEE", Locale.getDefault()).format(Date())
    }
    val currentDateStr = remember {
        SimpleDateFormat("MMMM d, yyyy", Locale.getDefault()).format(Date())
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        item { Spacer(modifier = Modifier.height(4.dp)) }

        // =================================================================
        // 1. "HI, {USER}!" - AT THE VERY TOP
        // =================================================================
        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Hi, ${user.username}!",
                        fontSize = 30.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = (-1).sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 2.dp)) {
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                        ) {
                            Text(
                                text = user.semesterStatus,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Bold,
                                fontSize = 10.sp,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                        if (PreferenceManager.getToken(context) == "cached_offline_token") {
                            Spacer(modifier = Modifier.width(6.dp))
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.8f)
                            ) {
                                Text(
                                    text = "Offline Mode",
                                    color = MaterialTheme.colorScheme.onErrorContainer,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 10.sp,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "• $currentDay",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }
        }

        // =================================================================
        // SYSTEM UPDATE NOTIFICATION BANNER (When Admin Publishes a Release)
        // =================================================================
        item {
            val latestRelease by UpdateManager.latestRelease.collectAsState()
            val mandatoryRequired by UpdateManager.mandatoryUpdateRequired.collectAsState()
            val hasNewerRelease = latestRelease != null && (latestRelease!!.versionCode > UpdateManager.CURRENT_VERSION_CODE || mandatoryRequired)

            if (hasNewerRelease && latestRelease != null) {
                val release = latestRelease!!
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = if (mandatoryRequired) MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.9f)
                        else MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.85f)
                    ),
                    shape = RoundedCornerShape(18.dp),
                    border = BorderStroke(1.dp, if (mandatoryRequired) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = if (mandatoryRequired) Icons.Default.SecurityUpdateWarning else Icons.Default.SystemUpdate,
                                    contentDescription = null,
                                    tint = if (mandatoryRequired) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary,
                                    modifier = Modifier.size(22.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = if (mandatoryRequired) "CRITICAL UPDATE MANDATORY" else "NEW SYSTEM UPDATE AVAILABLE",
                                    fontWeight = FontWeight.Black,
                                    fontSize = 12.sp,
                                    letterSpacing = 0.5.sp,
                                    color = if (mandatoryRequired) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = if (mandatoryRequired) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary
                            ) {
                                Text(
                                    text = "v${release.version}",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = release.releaseNotes ?: "A newer update is published in the Trace system archives. Download to ensure optimal stability and features.",
                            fontSize = 12.sp,
                            color = if (mandatoryRequired) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onSecondaryContainer,
                            maxLines = 3,
                            overflow = TextOverflow.Ellipsis
                        )

                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Size: ${release.fileSize}",
                                fontSize = 11.sp,
                                color = if (mandatoryRequired) MaterialTheme.colorScheme.onErrorContainer.copy(alpha = 0.8f) else MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.8f)
                            )
                            Button(
                                onClick = {
                                    UpdateManager.openDownloadUrl(context, release.downloadUrl)
                                },
                                shape = RoundedCornerShape(10.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (mandatoryRequired) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary
                                )
                            ) {
                                Icon(Icons.Default.Download, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("DOWNLOAD APK", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }

        // =================================================================
        // 2. ZENITH INSIGHT RECOMMENDATION (AI Personalized Strategy)
        // =================================================================
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.65f)
                ),
                shape = RoundedCornerShape(18.dp),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.35f))
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Surface(
                                shape = CircleShape,
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.2f),
                                modifier = Modifier.size(28.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        Icons.Default.AutoAwesome,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.primary,
                                        modifier = Modifier.size(16.dp)
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("ZENITH AI INSIGHT", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.primary)
                        }
                        Text("Live Guidance", fontSize = 9.sp, color = MaterialTheme.colorScheme.outline)
                    }

                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        recommendation,
                        style = MaterialTheme.typography.bodyMedium,
                        lineHeight = 20.sp,
                        fontSize = 13.sp
                    )

                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilledTonalButton(
                            onClick = { onNavigateToTab("socratic") },
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp),
                            modifier = Modifier.height(30.dp)
                        ) {
                            Icon(Icons.Default.Psychology, contentDescription = null, modifier = Modifier.size(13.dp))
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Ask Socratic Assistant", fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // =================================================================
        // 3. TODAY'S INTERACTIVE ACTIVITY HUB (Revamped with Direct Links)
        // =================================================================
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.DateRange, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Today's Tactical Hub", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
                    }
                    Text(currentDateStr, fontSize = 10.sp, color = MaterialTheme.colorScheme.outline)
                }

                TextButton(onClick = { onNavigateToTab("timetable") }) {
                    Text("Full Plan", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = null, modifier = Modifier.size(12.dp))
                }
            }
        }

        val todaysSlots = timetableUiState.weeklyPlan.filter { it.day.equals(currentDay, ignoreCase = true) }

        if (todaysSlots.isEmpty()) {
            item {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    shape = RoundedCornerShape(14.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(32.dp))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "No active sessions remaining for today. Rest & recharge for tomorrow!", 
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                            fontSize = 12.sp
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Button(onClick = { onNavigateToTab("assessment") }, shape = RoundedCornerShape(8.dp)) {
                            Text("Take Bonus Quiz", fontSize = 11.sp)
                        }
                    }
                }
            }
        } else {
            items(todaysSlots) { slot ->
                InteractiveTodaySlotCard(
                    slot = slot,
                    onLaunch = { targetTab, targetUnit ->
                        TactileFeedback.triggerSubtleClick(context)
                        if (targetTab == "learn" && targetUnit != null) {
                            val matchedUnit = uiState.unitsWithModules.find { it.unit.unitName.contains(targetUnit, ignoreCase = true) }
                            if (matchedUnit != null) {
                                onLaunchUnit(matchedUnit.unit.localId)
                            } else {
                                onNavigateToTab("assessment")
                            }
                        } else {
                            onNavigateToTab(targetTab)
                        }
                    }
                )
            }
        }

        // =================================================================
        // 4. LEARNING "PROGRESS" - CONCENTRIC RINGS & ACTIVE UNITS
        // =================================================================
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.School, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Curriculum Progress", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
                }
                Text("${uiState.unitsWithModules.size} Active Units", fontSize = 11.sp, color = MaterialTheme.colorScheme.outline)
            }
        }

        if (uiState.unitsWithModules.isEmpty() && !uiState.isLoading) {
            item {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    shape = RoundedCornerShape(14.dp)
                ) {
                    Column(modifier = Modifier.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "No curriculum units active on your profile yet.", 
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center,
                            fontSize = 12.sp
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Button(onClick = onOpenLibrary, shape = RoundedCornerShape(10.dp)) {
                            Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text("ADD FROM CURRICULUM CATALOGUE", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // Concentric Rings Unit Cards grouped by Exact Field -> Course -> Unit Group
        val groupedByField = uiState.unitsWithModules.groupBy { it.unit.exactFieldName }
        groupedByField.forEach { (fieldName, fieldUnits) ->
            item {
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 10.dp, bottom = 4.dp),
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            val fieldIcon = if (fieldName.contains("Medicine", ignoreCase = true)) Icons.Default.MedicalServices
                            else if (fieldName.contains("Computer", ignoreCase = true)) Icons.Default.Computer
                            else Icons.Default.Public
                            Icon(fieldIcon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = fieldName,
                                fontWeight = FontWeight.Black,
                                fontSize = 13.sp,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                        Text(
                            text = "${fieldUnits.size} Active",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }

            val groupedByCourse = fieldUnits.groupBy { it.unit.exactCourseName }
            groupedByCourse.forEach { (courseName, courseUnits) ->
                item {
                    Text(
                        text = "• Course: $courseName",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = MaterialTheme.colorScheme.secondary,
                        modifier = Modifier.padding(start = 6.dp, top = 2.dp, bottom = 4.dp)
                    )
                }

                items(courseUnits) { unitWithModules ->
                    val unit = unitWithModules.unit
                    val allTopics = unitWithModules.modules.flatMap { it.topics }
                    val allSubtopics = allTopics.flatMap { it.subtopics }
                    
                    val unitProgress = if (allSubtopics.isNotEmpty()) {
                        (allSubtopics.count { it.isCompleted }.toFloat() / allSubtopics.size) * 100f
                    } else 0f

                    val completedQuizSubtopicsCount = allSubtopics.count { sub ->
                        quizHistory.any { q -> q.unitName.equals(sub.name, ignoreCase = true) }
                    }
                    val quizProgress = if (allSubtopics.isNotEmpty()) {
                        (completedQuizSubtopicsCount.toFloat() / allSubtopics.size) * 100f
                    } else 0f

                    val currentModule = unitWithModules.modules.firstOrNull()

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onLaunchUnit(unit.localId) },
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)),
                        shape = RoundedCornerShape(16.dp),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.15f))
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            val rings = listOf(
                                RingProgress(unitProgress, MaterialTheme.colorScheme.primary, "Learnt"),
                                RingProgress(quizProgress, MaterialTheme.colorScheme.secondary, "Quiz")
                            )
                            
                            ProgressRings(
                                rings = rings,
                                learntProgress = unitProgress,
                                quizProgress = quizProgress,
                                modifier = Modifier.size(125.dp)
                            )
                            
                            Spacer(modifier = Modifier.width(16.dp))
                            
                            Column(modifier = Modifier.weight(1f)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Surface(
                                        shape = RoundedCornerShape(4.dp),
                                        color = MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)
                                    ) {
                                        Text(
                                            text = fieldName.uppercase(),
                                            fontSize = 8.sp,
                                            fontWeight = FontWeight.Black,
                                            color = MaterialTheme.colorScheme.primary,
                                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Surface(
                                        shape = RoundedCornerShape(4.dp),
                                        color = MaterialTheme.colorScheme.secondary.copy(alpha = 0.15f)
                                    ) {
                                        Text(
                                            text = courseName,
                                            fontSize = 8.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = MaterialTheme.colorScheme.secondary,
                                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    unit.unitName, 
                                    fontWeight = FontWeight.ExtraBold, 
                                    fontSize = 15.sp,
                                    lineHeight = 19.sp,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    currentModule?.module?.name ?: "Active Syllabus Module", 
                                    style = MaterialTheme.typography.bodySmall,
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.outline,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                                Spacer(modifier = Modifier.height(10.dp))
                                Button(
                                    onClick = { onLaunchUnit(unit.localId) },
                                    shape = RoundedCornerShape(8.dp),
                                    modifier = Modifier.fillMaxWidth().height(36.dp),
                                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                                ) {
                                    Text("CONTINUE SYLLABUS", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }
        }
        
        item { Spacer(modifier = Modifier.height(32.dp)) }
    }
}

/**
 * Appealing, interactive Today Activity Card that acts as a direct link to features around the app!
 */
@Composable
fun InteractiveTodaySlotCard(
    slot: ApiTimetableSlot,
    onLaunch: (tabName: String, unitName: String?) -> Unit
) {
    val activityLower = slot.activity.lowercase()
    val typeLower = slot.type.lowercase()

    val (actionLabel, targetTab, accentColor, icon) = when {
        activityLower.contains("quiz") || activityLower.contains("assessment") || typeLower.contains("assessment") -> {
            Quadruple("TAKE QUIZ", "assessment", Color(0xFF10B981), Icons.Default.School)
        }
        activityLower.contains("socratic") || activityLower.contains("assistant") || activityLower.contains("consultation") -> {
            Quadruple("START CHAT", "socratic", Color(0xFF00E5FF), Icons.Default.Psychology)
        }
        activityLower.contains("peer") || activityLower.contains("connect") || activityLower.contains("review") -> {
            Quadruple("CONNECT", "connect", Color(0xFF6366F1), Icons.Default.Group)
        }
        activityLower.contains("break") || typeLower.contains("break") -> {
            Quadruple("REST", "timetable", Color(0xFFF59E0B), Icons.Default.Coffee)
        }
        else -> {
            Quadruple("STUDY UNIT", "learn", MaterialTheme.colorScheme.primary, Icons.Default.MenuBook)
        }
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onLaunch(targetTab, slot.unit) },
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
        ),
        shape = RoundedCornerShape(14.dp),
        border = BorderStroke(1.dp, accentColor.copy(alpha = 0.35f))
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                shape = CircleShape,
                color = accentColor.copy(alpha = 0.15f),
                modifier = Modifier.size(40.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = accentColor,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = slot.time,
                        fontWeight = FontWeight.ExtraBold,
                        color = accentColor,
                        fontSize = 11.sp
                    )
                    slot.unit?.let { unitName ->
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "• $unitName",
                            fontSize = 10.sp,
                            color = MaterialTheme.colorScheme.outline,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = slot.activity,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            FilledTonalButton(
                onClick = { onLaunch(targetTab, slot.unit) },
                shape = RoundedCornerShape(8.dp),
                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp),
                modifier = Modifier.height(32.dp),
                colors = ButtonDefaults.filledTonalButtonColors(
                    containerColor = accentColor.copy(alpha = 0.15f),
                    contentColor = accentColor
                )
            ) {
                Text(actionLabel, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold)
                Spacer(modifier = Modifier.width(4.dp))
                Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = null, modifier = Modifier.size(12.dp))
            }
        }
    }
}

data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)
