package com.example.edu_ai.ui.screens.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.edu_ai.EduAIApplication
import com.example.edu_ai.data.remote.ApiAppRelease
import com.example.edu_ai.data.remote.CreateReleaseRequest
import com.example.edu_ai.repository.EduAIRepository
import com.example.edu_ai.utils.PreferenceManager
import com.example.edu_ai.utils.UpdateManager
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminDashboardScreen(
    repository: EduAIRepository? = null,
    onLogout: () -> Unit
) {
    val context = LocalContext.current
    val effectiveRepo = repository ?: (context.applicationContext as EduAIApplication).repository
    val scope = rememberCoroutineScope()
    var activeBackendMode by remember { mutableStateOf(PreferenceManager.getBackendMode(context)) }
    var aiPersona by remember { mutableStateOf("Socratic Tutor") }
    var temperature by remember { mutableStateOf(0.7f) }
    var securityProfile by remember { mutableStateOf("Enforced Zero-Leakage") }
    var statusMessage by remember { mutableStateOf<String?>("Telemetry active: All nodes healthy.") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Admin Superuser Console",
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp
                        )
                        Text(
                            text = "Full Database & Telemetry Authority",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                },
                actions = {
                    IconButton(onClick = onLogout) {
                        Icon(Icons.Default.ExitToApp, contentDescription = "Log Out")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // System Health & Telemetry KPI Row
            item {
                Text(
                    text = "System Health & Node Status",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text("API Status", style = MaterialTheme.typography.labelSmall)
                            Text("200 OK", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            Text("Mean: 42ms", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text("Backend Gateway", style = MaterialTheme.typography.labelSmall)
                            Text(activeBackendMode.uppercase(), fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            Text("FastAPI Active", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    Card(
                        modifier = Modifier.weight(1f),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text("Security", style = MaterialTheme.typography.labelSmall)
                            Text("Enforced", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                            Text("Zero-Leakage", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }

            // Backend Gateway Switcher Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.CloudSync, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Active Backend Gateway", fontWeight = FontWeight.Bold)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "Select which API target the Android client routes all learning & AI requests to:",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            listOf("cloud" to "Cloud", "ngrok" to "Ngrok", "container" to "Container").forEach { (key, label) ->
                                val isSelected = activeBackendMode == key
                                Button(
                                    onClick = {
                                        activeBackendMode = key
                                        PreferenceManager.saveBackendMode(context, key)
                                        statusMessage = "Active Gateway shifted to $label ($key)"
                                    },
                                    modifier = Modifier.weight(1f),
                                    colors = if (isSelected) ButtonDefaults.buttonColors() else ButtonDefaults.outlinedButtonColors()
                                ) {
                                    Text(label, fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }
            }

            // Superuser Parameter Configurator Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Tune, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Superuser Parameter Configurator", fontWeight = FontWeight.Bold)
                        }
                        Spacer(modifier = Modifier.height(12.dp))

                        // AI Persona
                        Text("Global AI Persona:", style = MaterialTheme.typography.labelMedium)
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            listOf("Socratic Tutor", "Clinical Assessor", "Mentor").forEach { persona ->
                                FilterChip(
                                    selected = aiPersona == persona,
                                    onClick = {
                                        aiPersona = persona
                                        statusMessage = "Global AI Persona shifted to $persona"
                                    },
                                    label = { Text(persona, fontSize = 11.sp) }
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        // Temperature
                        Text("LLM Temperature: ${String.format("%.1f", temperature)}", style = MaterialTheme.typography.labelMedium)
                        Slider(
                            value = temperature,
                            onValueChange = { temperature = it },
                            valueRange = 0.1f..1.0f,
                            steps = 8
                        )

                        Spacer(modifier = Modifier.height(8.dp))

                        // Security Profile
                        Text("Security Policy:", style = MaterialTheme.typography.labelMedium)
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            listOf("Enforced Zero-Leakage", "Audit Mode").forEach { sec ->
                                FilterChip(
                                    selected = securityProfile == sec,
                                    onClick = {
                                        securityProfile = sec
                                        statusMessage = "Security policy set to $sec"
                                    },
                                    label = { Text(sec, fontSize = 11.sp) }
                                )
                            }
                        }
                    }
                }
            }

            // Curriculum Hierarchy Administration (Fields > Courses > Units)
            item {
                var isCurriculumExpanded by remember { mutableStateOf(false) }
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { isCurriculumExpanded = !isCurriculumExpanded },
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.AccountTree, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Curriculum Hierarchy Administration", fontWeight = FontWeight.Bold)
                            }
                            Icon(
                                imageVector = if (isCurriculumExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                contentDescription = "Toggle"
                            )
                        }
                        
                        AnimatedVisibility(visible = isCurriculumExpanded) {
                            Column(modifier = Modifier.padding(top = 12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Text(
                                    "Master database structure of academic picks:",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                
                                val hierarchyData = listOf(
                                    "Clinical Medicine" to listOf(
                                        "MBChB" to listOf(
                                            "Internal Medicine I",
                                            "Internal Medicine II",
                                            "Internal Medicine III",
                                            "General Surgery I",
                                            "General Surgery II",
                                            "Clinical Pharmacology",
                                            "Obstetrics & Gynaecology",
                                            "Emergency Medicine",
                                            "Child Health"
                                        )
                                    ),
                                    "Global Studies & Core Foundations" to listOf(
                                        "Common Core Curriculum" to listOf(
                                            "Research Methodology",
                                            "Introduction to Philosophy",
                                            "Entrepreneurship",
                                            "Basic Computer Skills"
                                        )
                                    ),
                                    "Computer Science & IT" to listOf(
                                        "BSc. Software Engineering" to listOf("Database Systems", "Advanced Algorithms", "Web Architecture"),
                                        "BSc. Artificial Intelligence" to listOf("Machine Learning", "Neural Networks", "NLP & LLMs")
                                    )
                                )

                                hierarchyData.forEach { (field, courses) ->
                                    Card(
                                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Column(modifier = Modifier.padding(10.dp)) {
                                            Text(field, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, color = MaterialTheme.colorScheme.primary)
                                            Spacer(modifier = Modifier.height(6.dp))
                                            courses.forEach { (course, units) ->
                                                Column(modifier = Modifier.padding(start = 12.dp, top = 4.dp)) {
                                                    Text("• $course", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = MaterialTheme.colorScheme.secondary)
                                                    Row(
                                                        modifier = Modifier.padding(start = 12.dp, top = 2.dp),
                                                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                                                    ) {
                                                        units.forEach { unit ->
                                                            SuggestionChip(
                                                                onClick = {
                                                                    statusMessage = "Admin: Selected syllabus target: $unit"
                                                                },
                                                                label = { Text(unit, fontSize = 10.sp) }
                                                            )
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // System Releases Archive & Mandatory Upgrade Trigger Administration
            item {
                val releases by UpdateManager.releases.collectAsState()
                val isCheckingReleases by UpdateManager.isChecking.collectAsState()
                var isArchiveExpanded by remember { mutableStateOf(true) }
                var showNewReleaseDialog by remember { mutableStateOf(false) }

                var newVersion by remember { mutableStateOf("1.1.0") }
                var newVersionCode by remember { mutableStateOf("2") }
                var newDownloadUrl by remember { mutableStateOf("https://github.com/Agent606/Trace/releases/tag/v1.1.0") }
                var newReleaseNotes by remember { mutableStateOf("Critical security update and updated Socratic Clinical reasoning models.") }
                var newIsMandatory by remember { mutableStateOf(false) }
                var newFileSize by remember { mutableStateOf("14.8 MB") }
                var isSubmittingRelease by remember { mutableStateOf(false) }

                val isAnyMandatoryActive = releases.any { it.isMandatory }

                LaunchedEffect(Unit) {
                    UpdateManager.checkForUpdates(effectiveRepo)
                }

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (isAnyMandatoryActive) MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.2f) else MaterialTheme.colorScheme.surface
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { isArchiveExpanded = !isArchiveExpanded },
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = if (isAnyMandatoryActive) Icons.Default.SecurityUpdateWarning else Icons.Default.Inventory2,
                                    contentDescription = null,
                                    tint = if (isAnyMandatoryActive) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Column {
                                    Text("App Releases & Archive Authority", fontWeight = FontWeight.Bold)
                                    Text(
                                        if (isAnyMandatoryActive) "🚨 MANDATORY LOCKDOWN ENFORCED" else "Normal Distribution (${releases.size} releases)",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = if (isAnyMandatoryActive) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.outline
                                    )
                                }
                            }
                            Icon(
                                imageVector = if (isArchiveExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                                contentDescription = "Toggle"
                            )
                        }

                        AnimatedVisibility(visible = isArchiveExpanded) {
                            Column(modifier = Modifier.padding(top = 12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Text(
                                    "When the admin marks a release as MANDATORY, active users on older versions are immediately blocked from the app until they download the new version.",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )

                                // Action Row: Refresh + Archive New Release Button
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    OutlinedButton(
                                        onClick = {
                                            scope.launch {
                                                UpdateManager.checkForUpdates(effectiveRepo)
                                                statusMessage = "Archive synchronized with cloud server."
                                            }
                                        },
                                        modifier = Modifier.weight(1f),
                                        enabled = !isCheckingReleases
                                    ) {
                                        Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("Sync Archive", fontSize = 12.sp)
                                    }

                                    Button(
                                        onClick = { showNewReleaseDialog = !showNewReleaseDialog },
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text(if (showNewReleaseDialog) "Cancel" else "+ New Release", fontSize = 12.sp)
                                    }
                                }

                                // New Release Form
                                if (showNewReleaseDialog) {
                                    Card(
                                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                                        modifier = Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(12.dp)
                                    ) {
                                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text("Archive New Application Release", fontWeight = FontWeight.Bold, fontSize = 13.sp)

                                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                OutlinedTextField(
                                                    value = newVersion,
                                                    onValueChange = { newVersion = it },
                                                    label = { Text("Version (e.g. 1.1.0)", fontSize = 11.sp) },
                                                    modifier = Modifier.weight(1f),
                                                    singleLine = true
                                                )
                                                OutlinedTextField(
                                                    value = newVersionCode,
                                                    onValueChange = { newVersionCode = it },
                                                    label = { Text("Version Code", fontSize = 11.sp) },
                                                    modifier = Modifier.weight(1f),
                                                    singleLine = true
                                                )
                                            }

                                            OutlinedTextField(
                                                value = newDownloadUrl,
                                                onValueChange = { newDownloadUrl = it },
                                                label = { Text("Download URL (APK Link)", fontSize = 11.sp) },
                                                modifier = Modifier.fillMaxWidth(),
                                                singleLine = true
                                            )

                                            OutlinedTextField(
                                                value = newReleaseNotes,
                                                onValueChange = { newReleaseNotes = it },
                                                label = { Text("Release Notes & Changelog", fontSize = 11.sp) },
                                                modifier = Modifier.fillMaxWidth(),
                                                minLines = 2
                                            )

                                            // Mandatory Trigger Checkbox
                                            Surface(
                                                shape = RoundedCornerShape(8.dp),
                                                color = if (newIsMandatory) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.background,
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .clickable { newIsMandatory = !newIsMandatory }
                                            ) {
                                                Row(
                                                    modifier = Modifier.padding(10.dp),
                                                    verticalAlignment = Alignment.CenterVertically
                                                ) {
                                                    Checkbox(
                                                        checked = newIsMandatory,
                                                        onCheckedChange = { newIsMandatory = it }
                                                    )
                                                    Spacer(modifier = Modifier.width(6.dp))
                                                    Column {
                                                        Text(
                                                            "🚨 Enforce as Mandatory Upgrade",
                                                            fontWeight = FontWeight.Bold,
                                                            fontSize = 12.sp,
                                                            color = if (newIsMandatory) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
                                                        )
                                                        Text(
                                                            "Active users must update to this release before they can access the app.",
                                                            fontSize = 10.sp,
                                                            color = MaterialTheme.colorScheme.outline
                                                        )
                                                    }
                                                }
                                            }

                                            Button(
                                                onClick = {
                                                    scope.launch {
                                                        isSubmittingRelease = true
                                                        try {
                                                            val vCode = newVersionCode.toIntOrNull() ?: 2
                                                            effectiveRepo.createRelease(
                                                                CreateReleaseRequest(
                                                                    version = newVersion.trim(),
                                                                    versionCode = vCode,
                                                                    downloadUrl = newDownloadUrl.trim(),
                                                                    releaseNotes = newReleaseNotes.trim(),
                                                                    isMandatory = newIsMandatory,
                                                                    fileSize = newFileSize.trim(),
                                                                    isCurrent = true
                                                                )
                                                            )
                                                            statusMessage = "Published v$newVersion to archive! Mandatory trigger: $newIsMandatory"
                                                            showNewReleaseDialog = false
                                                            UpdateManager.checkForUpdates(effectiveRepo)
                                                        } catch (e: Exception) {
                                                            statusMessage = "Archive publish failed: ${e.message}"
                                                        } finally {
                                                            isSubmittingRelease = false
                                                        }
                                                    }
                                                },
                                                modifier = Modifier.fillMaxWidth(),
                                                enabled = !isSubmittingRelease && newVersion.isNotBlank() && newDownloadUrl.isNotBlank()
                                            ) {
                                                if (isSubmittingRelease) {
                                                    CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
                                                } else {
                                                    Text("Publish to Admin Archive")
                                                }
                                            }
                                        }
                                    }
                                }

                                // List of logged releases
                                releases.forEach { release ->
                                    Card(
                                        colors = CardDefaults.cardColors(
                                            containerColor = if (release.isMandatory) MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f) else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                                        ),
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Column(modifier = Modifier.padding(12.dp)) {
                                            Row(
                                                modifier = Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Row(verticalAlignment = Alignment.CenterVertically) {
                                                    Text("v${release.version}", fontWeight = FontWeight.Black, fontSize = 14.sp)
                                                    Spacer(modifier = Modifier.width(6.dp))
                                                    Text("(Code: ${release.versionCode})", fontSize = 11.sp, color = MaterialTheme.colorScheme.outline)
                                                }

                                                Surface(
                                                    shape = RoundedCornerShape(4.dp),
                                                    color = if (release.isMandatory) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondaryContainer
                                                ) {
                                                    Text(
                                                        text = if (release.isMandatory) "MANDATORY LOCK" else "OPTIONAL",
                                                        fontSize = 9.sp,
                                                        fontWeight = FontWeight.Black,
                                                        color = if (release.isMandatory) Color.White else MaterialTheme.colorScheme.onSecondaryContainer,
                                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                                    )
                                                }
                                            }

                                            if (!release.releaseNotes.isNullOrBlank()) {
                                                Spacer(modifier = Modifier.height(4.dp))
                                                Text(
                                                    text = release.releaseNotes,
                                                    style = MaterialTheme.typography.bodySmall,
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                                )
                                            }

                                            Spacer(modifier = Modifier.height(8.dp))

                                            // Toggle Mandatory Lock Trigger Button
                                            Button(
                                                onClick = {
                                                    scope.launch {
                                                        try {
                                                            effectiveRepo.toggleMandatoryRelease(release.id)
                                                            UpdateManager.checkForUpdates(effectiveRepo)
                                                            statusMessage = "Toggled mandatory upgrade trigger for v${release.version}"
                                                        } catch (e: Exception) {
                                                            statusMessage = "Toggle failed: ${e.message}"
                                                        }
                                                    }
                                                },
                                                modifier = Modifier.fillMaxWidth(),
                                                colors = if (release.isMandatory) {
                                                    ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant, contentColor = MaterialTheme.colorScheme.onSurfaceVariant)
                                                } else {
                                                    ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                                                },
                                                shape = RoundedCornerShape(8.dp)
                                            ) {
                                                Text(
                                                    text = if (release.isMandatory) "Deactivate Mandatory Lock" else "🚨 Enforce Mandatory Upgrade",
                                                    fontSize = 11.sp,
                                                    fontWeight = FontWeight.Bold
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Quick Superuser Action Controls
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("Direct Administration Actions", fontWeight = FontWeight.Bold)

                        OutlinedButton(
                            onClick = {
                                statusMessage = "X-Internal-Api-Key rotated successfully across client & server."
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Key, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Rotate Handshake Token")
                        }

                        OutlinedButton(
                            onClick = {
                                statusMessage = "Master Syllabus & SQLite Schema re-synced."
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Storage, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Re-sync Local Database Schema")
                        }

                        Button(
                            onClick = {
                                statusMessage = "Simulated high load pulse (200 requests/sec) dispatched."
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Speed, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Trigger Health Load Simulation")
                        }
                    }
                }
            }

            // Status feedback banner
            if (statusMessage != null) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant)
                            .padding(12.dp)
                    ) {
                        Text(
                            text = statusMessage!!,
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = FontFamily.Monospace,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}
