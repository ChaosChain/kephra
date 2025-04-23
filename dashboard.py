"""
Kephra Web Dashboard

A simple web interface to monitor and control Kephra's autonomous agents.
"""
import os
import asyncio
import json
import logging
import time
import queue
from datetime import datetime, timedelta
from threading import Thread
import subprocess
import webbrowser
import random
import sys

# Add the project root directory to the path so imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.protocol_analyzer.metrics_analyzer import MetricsAnalyzer
from src.protocol_analyzer.protocol_data_manager import ProtocolDataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Kephra Dashboard")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Configure templates
templates = Jinja2Templates(directory="templates")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# State for the system
kephra_process = None
log_buffer = []
MAX_LOG_ENTRIES = 1000
active_proposals = {}
github_issues = []

# Use a queue for thread-safe communication
message_queue = queue.Queue()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    # Create the dashboard HTML template
    with open("templates/dashboard.html", "w") as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kephra</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #3949ab;
            --secondary-color: #5c6bc0;
            --success-color: #43a047;
            --warning-color: #ffa000;
            --danger-color: #e53935;
            --light-bg: #f5f7fa;
            --dark-text: #37474f;
            --card-shadow: 0 4px 6px rgba(0,0,0,0.08);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--light-bg);
            color: var(--dark-text);
            min-height: 100vh;
        }
        
        .navbar {
            background-color: var(--primary-color);
            box-shadow: var(--card-shadow);
        }
        
        .sidebar {
            background-color: #fff;
            box-shadow: var(--card-shadow);
            border-radius: 12px;
            padding: 0;
            overflow: hidden;
        }
        
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s;
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-4px);
        }
        
        .card-header {
            background-color: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 15px 20px;
            font-weight: 600;
        }
        
        .eip-card .card-header {
            border-left: 4px solid var(--primary-color);
        }
        
        .github-card .card-header {
            border-left: 4px solid var(--success-color);
        }
        
        .agent-card .card-header {
            border-left: 4px solid var(--warning-color);
        }
        
        .logs-container {
            max-height: 200px;
            overflow-y: auto;
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            font-family: monospace;
            font-size: 12px;
            margin-top: 10px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-active {
            background-color: var(--success-color);
        }
        
        .status-inactive {
            background-color: var(--danger-color);
        }
        
        .status-pending {
            background-color: var(--warning-color);
        }
        
        .tab-content {
            padding: 20px;
            background: #fff;
            border-radius: 0 0 12px 12px;
        }
        
        .nav-tabs {
            border: none;
            padding: 0 20px;
            background: #fff;
            border-radius: 12px 12px 0 0;
        }
        
        .nav-tabs .nav-link {
            border: none;
            color: var(--dark-text);
            padding: 15px 20px;
            font-weight: 500;
        }
        
        .nav-tabs .nav-link.active {
            color: var(--primary-color);
            background: transparent;
            border-bottom: 3px solid var(--primary-color);
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .agent-item {
            background: #fff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: var(--card-shadow);
            border-left: 4px solid var(--secondary-color);
            transition: transform 0.2s;
        }
        
        .agent-item:hover {
            transform: translateY(-4px);
        }
        
        .eip-view {
            background: #fff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .eip-content {
            max-height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            font-family: monospace;
            white-space: pre-wrap;
            margin-top: 15px;
        }
        
        .issue-badge {
            display: inline-block;
            border-radius: 16px;
            padding: 4px 12px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        
        .priority-high {
            background-color: rgba(229, 57, 53, 0.1);
            color: #e53935;
        }
        
        .priority-medium {
            background-color: rgba(255, 160, 0, 0.1);
            color: #ffa000;
        }
        
        .priority-low {
            background-color: rgba(67, 160, 71, 0.1);
            color: #43a047;
        }
        
        .eip-detail {
            padding: 10px 15px;
            background: rgba(57, 73, 171, 0.05);
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .eip-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .eip-meta-item {
            background: rgba(92, 107, 192, 0.1);
            color: var(--primary-color);
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="#">
                <span class="fs-4">Kephra <span class="text-light fw-light">EIP Generator</span></span>
            </a>
            <div class="d-flex align-items-center">
                <span class="navbar-text me-3 text-light">
                    <span class="status-indicator" id="system-status"></span>
                    <span id="status-text">Initializing...</span>
                </span>
                <button class="btn btn-outline-light me-2" id="start-btn">
                    <i class="fas fa-play me-1"></i> Start
                </button>
                <button class="btn btn-outline-light" id="stop-btn">
                    <i class="fas fa-stop me-1"></i> Stop
                </button>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body p-0">
                        <ul class="nav nav-tabs" id="mainTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="dashboard-tab" data-bs-toggle="tab" data-bs-target="#dashboard" type="button" role="tab">
                                    <i class="fas fa-chart-line me-2"></i>Dashboard
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="eips-tab" data-bs-toggle="tab" data-bs-target="#eips" type="button" role="tab">
                                    <i class="fas fa-file-code me-2"></i>Generated EIPs
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="issues-tab" data-bs-toggle="tab" data-bs-target="#issues" type="button" role="tab">
                                    <i class="fas fa-exclamation-circle me-2"></i>GitHub Issues
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="logs-tab" data-bs-toggle="tab" data-bs-target="#logs-tab-content" type="button" role="tab">
                                    <i class="fas fa-terminal me-2"></i>System Logs
                                </button>
                            </li>
                        </ul>
                        <div class="tab-content" id="mainTabsContent">
                            <!-- Dashboard Tab -->
                            <div class="tab-pane fade show active" id="dashboard" role="tabpanel">
                                <h4 class="mb-4">Agent Activities</h4>
                                <div id="agents-container" class="agents-grid">
                                    <!-- Agents will be populated here -->
                                    <div class="text-center text-muted py-5">
                                        <i class="fas fa-robot fa-3x mb-3 text-secondary opacity-50"></i>
                                        <p>No active agents</p>
                                    </div>
                                </div>
                                
                                <div class="row mt-4">
                                    <div class="col-md-6">
                                        <div class="card github-card">
                                            <div class="card-header d-flex justify-content-between align-items-center">
                                                <h5 class="mb-0">
                                                    <i class="fab fa-github me-2"></i>Latest Issues
                                                </h5>
                                                <span class="badge bg-primary" id="issues-count">0</span>
                                            </div>
                                            <div class="card-body">
                                                <div id="github-issues-preview" style="max-height: 300px; overflow-y: auto;">
                                                    <!-- Latest issues preview -->
                                                    <div class="text-center text-muted py-4">
                                                        <i class="fas fa-search fa-2x mb-3 text-secondary opacity-50"></i>
                                                        <p>No issues found yet</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="col-md-6">
                                        <div class="card eip-card">
                                            <div class="card-header d-flex justify-content-between align-items-center">
                                                <h5 class="mb-0">
                                                    <i class="fas fa-file-code me-2"></i>Latest Proposals
                                                </h5>
                                                <span class="badge bg-primary" id="proposals-count">0</span>
                                            </div>
                                            <div class="card-body">
                                                <div id="proposals-preview" style="max-height: 300px; overflow-y: auto;">
                                                    <!-- Latest proposals preview -->
                                                    <div class="text-center text-muted py-4">
                                                        <i class="fas fa-file-alt fa-2x mb-3 text-secondary opacity-50"></i>
                                                        <p>No proposals yet</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- EIPs Tab -->
                            <div class="tab-pane fade" id="eips" role="tabpanel">
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <h4>Generated EIP Proposals</h4>
                                    <span class="badge bg-primary fs-6" id="eips-count">0</span>
                                </div>
                                
                                <div id="eip-details">
                                    <!-- EIP details will go here -->
                                    <div class="text-center text-muted py-5">
                                        <i class="fas fa-file-alt fa-3x mb-3 text-secondary opacity-50"></i>
                                        <p>Select an EIP to view details</p>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-12">
                                        <div id="proposals-full">
                                            <!-- Full proposals list -->
                                            <div class="text-center text-muted py-5">
                                                <i class="fas fa-file-alt fa-3x mb-3 text-secondary opacity-50"></i>
                                                <p>No proposals generated yet</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Issues Tab -->
                            <div class="tab-pane fade" id="issues" role="tabpanel">
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <h4>GitHub Issues</h4>
                                    <span class="badge bg-primary fs-6" id="full-issues-count">0</span>
                                </div>
                                
                                <div id="github-issues-full">
                                    <!-- Full issues list -->
                                    <div class="text-center text-muted py-5">
                                        <i class="fas fa-exclamation-circle fa-3x mb-3 text-secondary opacity-50"></i>
                                        <p>No issues found yet</p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Logs Tab (Hidden by default) -->
                            <div class="tab-pane fade" id="logs-tab-content" role="tabpanel">
                                <h4 class="mb-3">System Logs</h4>
                                <div class="logs-container" id="logs">
                                    <!-- Logs will be populated here -->
                                    <div class="text-center text-muted py-3">
                                        <p>No logs available</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // WebSocket connection
        const socket = new WebSocket(`ws://${window.location.host}/ws`);
        const logsContainer = document.getElementById('logs');
        const githubIssuesPreview = document.getElementById('github-issues-preview');
        const githubIssuesFull = document.getElementById('github-issues-full');
        const proposalsPreview = document.getElementById('proposals-preview');
        const proposalsFull = document.getElementById('proposals-full');
        const agentsContainer = document.getElementById('agents-container');
        const eipDetails = document.getElementById('eip-details');
        const statusIndicator = document.getElementById('system-status');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const issuesCount = document.getElementById('issues-count');
        const fullIssuesCount = document.getElementById('full-issues-count');
        const proposalsCount = document.getElementById('proposals-count');
        const eipsCount = document.getElementById('eips-count');
        
        // Store full data
        let allProposals = {};
        let selectedEip = null;
        
        // Update system status UI
        function updateStatus(status) {
            if (status === 'active') {
                statusIndicator.className = 'status-indicator status-active';
                statusText.textContent = 'Running';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else if (status === 'inactive') {
                statusIndicator.className = 'status-indicator status-inactive';
                statusText.textContent = 'Stopped';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            } else {
                statusIndicator.className = 'status-indicator status-pending';
                statusText.textContent = 'Starting...';
                startBtn.disabled = true;
                stopBtn.disabled = true;
            }
        }
        
        // Add a log entry
        function addLogEntry(log) {
            // Remove placeholder if exists
            if (logsContainer.querySelector('.text-muted')) {
                logsContainer.innerHTML = '';
            }
            
            const entry = document.createElement('p');
            entry.className = 'log-entry m-0 py-1';
            entry.textContent = log;
            logsContainer.appendChild(entry);
            logsContainer.scrollTop = logsContainer.scrollHeight;
            
            // Limit the number of log entries
            while (logsContainer.children.length > 1000) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
        }
        
        // Update GitHub issues display (preview)
        function updateGithubIssuesPreview(issues) {
            if (!issues || issues.length === 0) {
                githubIssuesPreview.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-search fa-2x mb-3 text-secondary opacity-50"></i>
                        <p>No issues found yet</p>
                    </div>`;
                githubIssuesFull.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-exclamation-circle fa-3x mb-3 text-secondary opacity-50"></i>
                        <p>No issues found yet</p>
                    </div>`;
                issuesCount.textContent = '0';
                fullIssuesCount.textContent = '0';
                return;
            }
            
            // Count issues that need EIPs
            const needsEipCount = issues.filter(issue => issue.needs_eip).length;
            issuesCount.textContent = needsEipCount.toString();
            fullIssuesCount.textContent = issues.length.toString();
            
            // Preview - only show issues that need EIPs, limited to 5
            const previewIssues = issues.filter(issue => issue.needs_eip).slice(0, 5);
            
            if (previewIssues.length === 0) {
                githubIssuesPreview.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <p>No issues need EIPs currently</p>
                    </div>`;
            } else {
                githubIssuesPreview.innerHTML = '';
                previewIssues.forEach(issue => {
                    const card = document.createElement('div');
                    card.className = 'card mb-2 border-0 shadow-sm';
                    card.innerHTML = `
                        <div class="card-body p-3">
                            <h6 class="card-title mb-1">#${issue.number}: ${issue.title}</h6>
                            <p class="card-text small text-muted mb-1">${issue.body?.substring(0, 100) || ''}${issue.body?.length > 100 ? '...' : ''}</p>
                            <div class="mt-2">
                                <span class="badge bg-primary">Needs EIP</span>
                                ${(issue.labels || []).map(label => `
                                    <span class="badge bg-secondary">${label}</span>
                                `).join(' ')}
                            </div>
                        </div>
                    `;
                    githubIssuesPreview.appendChild(card);
                });
            }
            
            // Full issues list
            githubIssuesFull.innerHTML = '';
            issues.forEach(issue => {
                const needsEipBadge = issue.needs_eip ? '<span class="badge bg-primary me-2">Needs EIP</span>' : '';
                
                const card = document.createElement('div');
                card.className = 'card mb-3';
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h5 class="card-title mb-0">#${issue.number}: ${issue.title}</h5>
                            <div>${needsEipBadge}</div>
                        </div>
                        <p class="card-text">${issue.body || 'No description provided'}</p>
                        <div class="mt-3">
                            ${(issue.labels || []).map(label => `
                                <span class="badge bg-secondary me-1">${label}</span>
                            `).join('')}
                            <a href="https://github.com/${issue.repo ? `ethereum/${issue.repo}/issues/${issue.number}` : '#'}" 
                               class="btn btn-sm btn-outline-primary float-end" target="_blank">
                                <i class="fab fa-github me-1"></i> View on GitHub
                            </a>
                        </div>
                    </div>
                `;
                githubIssuesFull.appendChild(card);
            });
        }
        
        // Show EIP details
        function showEipDetails(eipId) {
            const proposal = allProposals[eipId];
            if (!proposal) return;
            
            selectedEip = eipId;
            
            // Update all proposal cards to remove active state
            document.querySelectorAll('.eip-proposal-card').forEach(card => {
                card.classList.remove('border-primary');
            });
            
            // Add active state to selected card
            const selectedCard = document.getElementById(`eip-card-${eipId}`);
            if (selectedCard) {
                selectedCard.classList.add('border-primary');
            }
            
            // Get EIP data
            const eipData = proposal.eip_data || {};
            
            // Check if we have full_content
            let contentHTML = '';
            
            // Special handling for auto-generated EIPs from logs
            if (proposal.is_generated) {
                if (eipData.full_content) {
                    contentHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-robot me-2"></i>
                            This EIP was automatically generated from GitHub issue #${proposal.issue_number}.
                            Check the <a href="#" onclick="document.getElementById('logs-tab').click();" class="alert-link">system logs</a> for details.
                        </div>
                        <div class="eip-detail">
                            <h5>Original Issue</h5>
                            <p><a href="https://github.com/ethereum/EIPs/issues/${proposal.issue_number}" target="_blank">#${proposal.issue_number}: ${proposal.issue_title}</a></p>
                        </div>
                        <div class="eip-content border rounded p-3 bg-light">
                            <pre class="mb-0">${eipData.full_content}</pre>
                        </div>
                    `;
                } else {
                    contentHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-robot me-2"></i>
                            This EIP was automatically generated from GitHub issue #${proposal.issue_number}.
                            Check the <a href="#" onclick="document.getElementById('logs-tab').click();" class="alert-link">system logs</a> for details.
                        </div>
                        <div class="eip-detail">
                            <h5>Original Issue</h5>
                            <p><a href="https://github.com/ethereum/EIPs/issues/${proposal.issue_number}" target="_blank">#${proposal.issue_number}: ${proposal.issue_title}</a></p>
                        </div>
                    `;
                }
            } 
            // Full content display for file-based EIPs
            else if (eipData.full_content) {
                contentHTML = `
                    <div class="eip-content border rounded p-3 bg-light">
                        <pre class="mb-0">${eipData.full_content}</pre>
                    </div>
                `;
            } 
            // Build sections from individual parts if full_content is not available
            else if (eipData.motivation || eipData.specification || eipData.rationale || eipData.implementation) {
                // Build sections from parts if we don't have full content
                if (eipData.motivation) {
                    contentHTML += `
                        <div class="eip-detail">
                            <h5>Motivation</h5>
                            <p>${eipData.motivation}</p>
                        </div>
                    `;
                }
                
                if (eipData.specification) {
                    contentHTML += `
                        <div class="eip-detail">
                            <h5>Specification</h5>
                            <p>${eipData.specification}</p>
                        </div>
                    `;
                }
                
                if (eipData.rationale) {
                    contentHTML += `
                        <div class="eip-detail">
                            <h5>Rationale</h5>
                            <p>${eipData.rationale}</p>
                        </div>
                    `;
                }
                
                if (eipData.implementation) {
                    contentHTML += `
                        <div class="eip-detail">
                            <h5>Implementation</h5>
                            <p>${eipData.implementation}</p>
                        </div>
                    `;
                }
            } else {
                contentHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Full EIP content not available.
                    </div>
                `;
            }
            
            eipDetails.innerHTML = `
                <div class="eip-view">
                    <h4 class="mb-3">${eipId}: ${eipData.title || 'Untitled'}</h4>
                    
                    <div class="eip-meta">
                        <div class="eip-meta-item">
                            <i class="fas fa-tag me-1"></i> ${eipData.status || 'Draft'}
                        </div>
                        <div class="eip-meta-item">
                            <i class="fas fa-code-branch me-1"></i> ${eipData.type || 'Standards Track'}
                        </div>
                        <div class="eip-meta-item">
                            <i class="fas fa-user me-1"></i> ${eipData.author || 'Unknown'}
                        </div>
                        <div class="eip-meta-item">
                            <i class="far fa-calendar-alt me-1"></i> Created: ${new Date(proposal.created_at).toLocaleDateString()}
                        </div>
                    </div>
                    
                    <div class="eip-detail">
                        <h5>Abstract</h5>
                        <p>${eipData.abstract || 'No abstract provided'}</p>
                    </div>
                    
                    ${contentHTML}
                    
                    ${proposal.file_path ? `
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <h5 class="mb-0">File Location</h5>
                            <span class="badge bg-light text-dark">${proposal.file_path}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        // Update proposals display
        function updateProposals(activeProposals) {
            // Store the full data
            allProposals = activeProposals || {};
            
            const proposalCount = Object.keys(allProposals).length;
            proposalsCount.textContent = proposalCount.toString();
            eipsCount.textContent = proposalCount.toString();
            
            if (proposalCount === 0) {
                proposalsPreview.innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="fas fa-file-alt fa-2x mb-3 text-secondary opacity-50"></i>
                        <p>No proposals yet</p>
                    </div>`;
                    
                proposalsFull.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-file-alt fa-3x mb-3 text-secondary opacity-50"></i>
                        <p>No proposals generated yet</p>
                    </div>`;
                
                // Clear EIP details if none selected
                if (!selectedEip || !allProposals[selectedEip]) {
                    eipDetails.innerHTML = `
                        <div class="text-center text-muted py-5">
                            <i class="fas fa-file-alt fa-3x mb-3 text-secondary opacity-50"></i>
                            <p>Select an EIP to view details</p>
                        </div>`;
                }
                
                return;
            }
            
            // Preview - show latest 5 proposals
            const previewProposalIds = Object.keys(allProposals).slice(0, 5);
            proposalsPreview.innerHTML = '';
            
            previewProposalIds.forEach(eipId => {
                const proposal = allProposals[eipId];
                const statusClass = 
                    proposal.status === 'draft' ? 'warning' :
                    proposal.status === 'submitted' ? 'info' :
                    proposal.status === 'reviewed' ? 'primary' : 'success';
                
                const card = document.createElement('div');
                card.className = 'card mb-2 border-0 shadow-sm';
                card.innerHTML = `
                    <div class="card-body p-3">
                        <h6 class="mb-1">${eipId}</h6>
                        <p class="small mb-1">${proposal.eip_data?.title || 'Untitled'}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-${statusClass}">${proposal.status}</span>
                            <small class="text-muted">${new Date(proposal.created_at).toLocaleDateString()}</small>
                        </div>
                    </div>
                `;
                proposalsPreview.appendChild(card);
            });
            
            // Full proposals list
            proposalsFull.innerHTML = '<div class="row row-cols-1 row-cols-md-2 g-4 mb-4">';
            
            Object.keys(allProposals).forEach(eipId => {
                const proposal = allProposals[eipId];
                const statusClass = 
                    proposal.status === 'draft' ? 'warning' :
                    proposal.status === 'submitted' ? 'info' :
                    proposal.status === 'reviewed' ? 'primary' : 'success';
                
                const isActive = selectedEip === eipId;
                
                proposalsFull.innerHTML += `
                    <div class="col">
                        <div id="eip-card-${eipId}" class="card h-100 eip-proposal-card ${isActive ? 'border-primary' : ''}">
                            <div class="card-body">
                                <h5 class="card-title">${eipId}</h5>
                                <h6 class="card-subtitle mb-2 text-muted">${proposal.eip_data?.title || 'Untitled'}</h6>
                                <p class="card-text small">${proposal.eip_data?.abstract?.substring(0, 120) || 'No abstract'}${proposal.eip_data?.abstract?.length > 120 ? '...' : ''}</p>
                            </div>
                            <div class="card-footer bg-transparent d-flex justify-content-between align-items-center">
                                <span class="badge bg-${statusClass}">${proposal.status}</span>
                                <button onclick="showEipDetails('${eipId}')" class="btn btn-sm btn-primary">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            proposalsFull.innerHTML += '</div>';
            
            // Show details of first EIP if none selected yet
            if (!selectedEip || !allProposals[selectedEip]) {
                const firstEipId = Object.keys(allProposals)[0];
                if (firstEipId) {
                    showEipDetails(firstEipId);
                }
            } else if (allProposals[selectedEip]) {
                // Update details of currently selected EIP
                showEipDetails(selectedEip);
            }
            
            // Add onclick handlers for EIP cards
            setTimeout(() => {
                document.querySelectorAll('.eip-proposal-card').forEach(card => {
                    const eipId = card.id.replace('eip-card-', '');
                    card.onclick = () => showEipDetails(eipId);
                });
            }, 100);
        }
        
        // Update agents display
        function updateAgents(agents) {
            if (!agents || Object.keys(agents).length === 0) {
                agentsContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-robot fa-3x mb-3 text-secondary opacity-50"></i>
                        <p>No active agents</p>
                    </div>`;
                return;
            }
            
            agentsContainer.innerHTML = '';
            
            for (const [agentId, agent] of Object.entries(agents)) {
                const agentTypeIcon = 
                    agent.agent_type === 'PROPOSER' ? 'fa-lightbulb' :
                    agent.agent_type === 'REVIEWER' ? 'fa-clipboard-check' :
                    agent.agent_type === 'SIMULATOR' ? 'fa-vial' :
                    agent.agent_type === 'CONSENSUS' ? 'fa-balance-scale' : 'fa-robot';
                
                const div = document.createElement('div');
                div.className = 'agent-item';
                div.innerHTML = `
                    <h6 class="mb-2">
                        <i class="fas ${agentTypeIcon} me-2"></i>
                        ${agent.name}
                    </h6>
                    <p class="text-muted small mb-2">${agent.role}</p>
                    <div class="mt-2">
                        <span class="badge bg-primary">${agent.agent_type}</span>
                    </div>
                `;
                agentsContainer.appendChild(div);
            }
        }
        
        // Handle WebSocket messages
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'log') {
                addLogEntry(data.content);
            } else if (data.type === 'github_issues') {
                updateGithubIssuesPreview(data.issues);
            } else if (data.type === 'proposals') {
                updateProposals(data.proposals);
            } else if (data.type === 'agents') {
                updateAgents(data.agents);
            } else if (data.type === 'status') {
                updateStatus(data.status);
            }
        };
        
        // Connect WebSocket
        socket.onopen = function(e) {
            console.log("WebSocket connection established");
            addLogEntry("[DASHBOARD] WebSocket connection established");
            
            // Request initial data
            socket.send(JSON.stringify({ action: 'get_status' }));
        };
        
        // Handle connection errors
        socket.onerror = function(error) {
            console.error("WebSocket error:", error);
            addLogEntry("[DASHBOARD] WebSocket error");
            updateStatus('inactive');
        };
        
        // Handle connection close
        socket.onclose = function(event) {
            if (event.wasClean) {
                console.log(`WebSocket connection closed cleanly, code=${event.code}, reason=${event.reason}`);
                addLogEntry(`[DASHBOARD] WebSocket connection closed: ${event.reason}`);
            } else {
                console.error('WebSocket connection died');
                addLogEntry("[DASHBOARD] WebSocket connection died");
            }
            updateStatus('inactive');
        };
        
        // Handle button clicks
        startBtn.addEventListener('click', function() {
            socket.send(JSON.stringify({ action: 'start' }));
            updateStatus('pending');
        });
        
        stopBtn.addEventListener('click', function() {
            socket.send(JSON.stringify({ action: 'stop' }));
            updateStatus('pending');
        });
        
        // Make showEipDetails global
        window.showEipDetails = showEipDetails;
        
        // Initial UI setup
        updateStatus('inactive');
    </script>
</body>
</html>
        """)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Start a background task to process messages from the queue
        background_task = asyncio.create_task(process_message_queue())
        
        while True:
            # Wait for any command from the client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("action") == "start":
                    # Start Kephra process if not running
                    await start_kephra()
                    
                elif message.get("action") == "stop":
                    # Stop Kephra process if running
                    await stop_kephra()
                    
                elif message.get("action") == "get_status":
                    # Send current status
                    await update_status()
                    
                # Send initial log buffer
                for log in log_buffer:
                    await websocket.send_text(json.dumps({
                        "type": "log",
                        "content": log
                    }))
                    
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    finally:
        # Cancel the background task when the websocket disconnects
        if 'background_task' in locals():
            background_task.cancel()

async def process_message_queue():
    """Process messages from the queue and broadcast them."""
    while True:
        try:
            # Non-blocking check for messages
            for _ in range(message_queue.qsize()):
                try:
                    message = message_queue.get_nowait()
                    message_queue.task_done()
                    
                    # Check if it's a special trigger message
                    if isinstance(message, str):
                        try:
                            data = json.loads(message)
                            if data.get("type") == "trigger_parse_issues":
                                # Schedule the parse_github_issues task
                                asyncio.create_task(parse_github_issues())
                                continue
                            elif data.get("type") == "trigger_parse_proposals":
                                # Schedule the parse_proposals task
                                asyncio.create_task(parse_proposals())
                                continue
                            elif data.get("type") == "trigger_parse_agents":
                                # Schedule the parse_agents task
                                asyncio.create_task(parse_agents())
                                continue
                        except json.JSONDecodeError:
                            pass  # Not JSON, broadcast as-is
                    
                    # Regular message, broadcast it
                    await manager.broadcast(message)
                except queue.Empty:
                    break
            # Short sleep to avoid busy waiting
            await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            # Clean exit when task is cancelled
            break
        except Exception as e:
            logger.error(f"Error processing message queue: {e}")
            await asyncio.sleep(1)  # Longer sleep on error

async def update_status():
    """Send current system status to all clients."""
    # Check if process is running
    is_running = kephra_process is not None and kephra_process.poll() is None
    
    # Send status
    await manager.broadcast(json.dumps({
        "type": "status",
        "status": "active" if is_running else "inactive"
    }))
    
    # Send GitHub issues
    await manager.broadcast(json.dumps({
        "type": "github_issues",
        "issues": github_issues
    }))
    
    # Send proposals
    await manager.broadcast(json.dumps({
        "type": "proposals",
        "proposals": active_proposals
    }))

async def start_kephra():
    """Start the Kephra process."""
    global kephra_process
    
    if kephra_process is not None and kephra_process.poll() is None:
        logger.info("Kephra is already running")
        return
    
    logger.info("Starting Kephra process with protocol metrics integration")
    
    # Generate protocol insights to influence EIP generation
    protocol_insights = await generate_protocol_insights()
    
    # Log how protocol metrics will influence EIP generation
    if protocol_insights:
        logger.info("Protocol metrics will influence EIP generation and evaluation")
        
        # Influence EIP prioritization based on protocol health
        if protocol_insights.snapshot:
            network_health = protocol_insights.snapshot.network_health_score
            economic_health = protocol_insights.snapshot.economic_health_score
            security_health = protocol_insights.snapshot.security_health_score or 0.0
            
            # Determine areas of focus based on health scores
            focus_areas = []
            if network_health < 0.7:
                focus_areas.append("Network Efficiency")
                logger.info(f"Low network health score ({network_health:.2f}): Prioritizing network efficiency EIPs")
            
            if economic_health < 0.7:
                focus_areas.append("Economic Mechanisms")
                logger.info(f"Low economic health score ({economic_health:.2f}): Prioritizing economic mechanism EIPs")
            
            if security_health < 0.7:
                focus_areas.append("Security Improvements")
                logger.info(f"Low security health score ({security_health:.2f}): Prioritizing security improvement EIPs")
            
            if focus_areas:
                logger.info(f"Protocol analysis suggests focusing on: {', '.join(focus_areas)}")
            else:
                logger.info("Protocol health scores indicate no urgent areas requiring EIPs")
    
    # Parse GitHub issues and proposals to immediately show data
    await parse_github_issues()
    await parse_proposals()
    
    # Start the process
    cmd = [
        "/Users/sumeet/Desktop/ChaosChain_labs/kephra/kenv/bin/python", 
        "-m", "src.main", "--autonomous", "--verbose"
    ]
    
    kephra_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered
        cwd=os.getcwd()
    )
    
    # Start log reader thread
    def read_logs():
        while kephra_process.poll() is None:
            line = kephra_process.stdout.readline()
            if line:
                line = line.strip()
                # Add to buffer
                if len(log_buffer) >= MAX_LOG_ENTRIES:
                    log_buffer.pop(0)
                log_buffer.append(line)
                
                # Add to message queue instead of direct broadcast
                message_queue.put(json.dumps({
                    "type": "log",
                    "content": line
                }))
                
                # Check for patterns to extract data
                if "Found" in line and "issues that need EIPs" in line:
                    # Parse the number of issues - add to queue instead of direct async call
                    message_queue.put(json.dumps({
                        "type": "trigger_parse_issues"
                    }))
                
                if "Generated EIP" in line:
                    # Parse EIP generation - add to queue instead of direct async call
                    message_queue.put(json.dumps({
                        "type": "trigger_parse_proposals"
                    }))
                    
                # Check for other agent activities and update their status
                if "processing input" in line or "initialized" in line:
                    message_queue.put(json.dumps({
                        "type": "trigger_parse_agents"
                    }))
    
    # Start the thread
    log_thread = Thread(target=read_logs)
    log_thread.daemon = True
    log_thread.start()
    
    # Update status
    await update_status()

async def stop_kephra():
    """Stop the Kephra process."""
    global kephra_process
    
    if kephra_process is None or kephra_process.poll() is not None:
        logger.info("Kephra is not running")
        return
    
    logger.info("Stopping Kephra process")
    
    # Terminate the process
    try:
        kephra_process.terminate()
        # Wait for process to exit
        for _ in range(5):  # Wait up to 5 seconds
            if kephra_process.poll() is not None:
                break
            await asyncio.sleep(1)
        
        # Force kill if still running
        if kephra_process.poll() is None:
            kephra_process.kill()
    except Exception as e:
        logger.error(f"Error stopping Kephra: {e}")
    
    kephra_process = None
    
    # Update status
    await update_status()

async def parse_github_issues():
    """Parse GitHub issues from logs or fetch directly from GitHub API."""
    global github_issues
    
    # Try to fetch real GitHub issues if token is available
    github_token = os.environ.get("GITHUB_TOKEN")
    github_owner = os.environ.get("GITHUB_OWNER", "ethereum")
    github_repos = json.loads(os.environ.get("GITHUB_REPOS", '["EIPs"]'))
    
    # Initialize with empty list
    github_issues = []
    issues_loaded = False
    
    if github_token:
        try:
            import requests
            import random
            
            all_issues = []
            
            # First, check logs for GitHub issues that have been processed
            issues_from_logs = set()
            for line in log_buffer:
                if "Generating EIP for issue #" in line:
                    try:
                        # Extract issue number and title
                        parts = line.split("Generating EIP for issue #")[1].split(":", 1)
                        issue_number = parts[0].strip()
                        issue_title = parts[1].strip() if len(parts) > 1 else "Unknown Issue"
                        issues_from_logs.add((issue_number, issue_title))
                    except Exception:
                        pass
            
            # Add issues from logs to our list first
            for issue_number, issue_title in issues_from_logs:
                all_issues.append({
                    "number": int(issue_number),
                    "title": issue_title,
                    "body": f"This issue was identified in logs. View it on GitHub: https://github.com/{github_owner}/EIPs/issues/{issue_number}",
                    "needs_eip": True,
                    "repo": "EIPs",
                    "labels": ["from-logs"],
                    "from_logs": True
                })
            
            if all_issues:
                issues_loaded = True
                logger.info(f"Loaded {len(all_issues)} issues from logs")
            
            # Then try to fetch from GitHub API
            for repo in github_repos:
                logger.info(f"Fetching issues from {github_owner}/{repo}")
                url = f"https://api.github.com/repos/{github_owner}/{repo}/issues"
                
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                # Add parameters to get more issues and include closed ones
                params = {
                    "state": "all",  # Get both open and closed issues
                    "per_page": 30   # Get more issues per page
                }
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    issues_data = response.json()
                    issues_loaded = True
                    
                    # Check each issue if it needs an EIP
                    for issue in issues_data:
                        # Skip pull requests
                        if "pull_request" in issue:
                            continue
                            
                        title = issue.get("title", "")
                        body = issue.get("body", "") or ""
                        issue_number = issue.get("number")
                        
                        # Skip if we already have this issue from logs
                        if any(i["number"] == issue_number for i in all_issues):
                            continue
                        
                        # Simple heuristic to check if issue needs EIP
                        # Real implementation would use NLP or more sophisticated rules
                        eip_keywords = [
                            "proposal", "eip", "standard", "improvement", "protocol", 
                            "new feature", "enhancement", "upgrade", "interface", 
                            "specification"
                        ]
                        
                        needs_eip = any(keyword in (title + " " + body).lower() for keyword in eip_keywords)
                        
                        # Get labels
                        labels = [label.get("name") for label in issue.get("labels", [])]
                        
                        processed_issue = {
                            "number": issue_number,
                            "title": title,
                            "body": body,
                            "needs_eip": needs_eip,
                            "repo": repo,
                            "labels": labels,
                            "created_at": issue.get("created_at"),
                            "from_api": True
                        }
                        
                        all_issues.append(processed_issue)
                    
                    logger.info(f"Fetched {len(issues_data)} issues from {github_owner}/{repo}")
                else:
                    logger.error(f"Error fetching issues: {response.status_code} - {response.text}")
                    raise Exception(f"GitHub API error: {response.status_code}")
                    
            # Update global issue list with real data
            github_issues = all_issues
            logger.info(f"Updated issues list with {len(all_issues)} GitHub issues")
            
        except Exception as e:
            logger.error(f"Error fetching GitHub issues: {str(e)}")
            logger.info("No GitHub issues loaded - enable a valid GitHub token in .env to fetch real issues")
    else:
        logger.info("No GitHub token found. Add GITHUB_TOKEN to your .env file to fetch real issues.")
    
    # Broadcast to clients
    await manager.broadcast(json.dumps({
        "type": "github_issues",
        "issues": github_issues
    }))

def get_mock_issues():
    """Return mock GitHub issues for demonstration."""
    # This function is kept for backward compatibility, but returns an empty list
    return []

async def parse_proposals():
    """Parse active proposals from logs."""
    global active_proposals
    import random
    
    # Load generated EIPs from workspace directory
    generated_eips = {}
    real_eips_found = False
    
    try:
        # Use the configured EIP directory from .env
        import os
        from pathlib import Path
        
        # Get path from env or use default
        eip_repo_path = os.environ.get("EIP_REPOSITORY_PATH", "eip_repo")
        eips_dir = Path(eip_repo_path) / "EIPS"
        
        # First, check logs for EIP generation
        draft_eips = {}
        processed_eip_logs = set()  # Track which log lines we've already processed
        
        # First pass - collect all issue titles and numbers
        issue_titles = {}
        for line in log_buffer:
            if "Generating EIP for issue #" in line:
                try:
                    # Extract issue number and title
                    parts = line.split("Generating EIP for issue #")[1].split(":", 1)
                    issue_number = parts[0].strip()
                    issue_title = parts[1].strip() if len(parts) > 1 else "Unknown Issue"
                    issue_titles[issue_number] = issue_title
                except Exception as e:
                    logger.error(f"Error parsing issue title from log: {e}")
        
        # Second pass - process actual EIP generation logs
        for line in log_buffer:
            if "Generated EIP" in line and line not in processed_eip_logs:
                processed_eip_logs.add(line)  # Mark this log line as processed
                
                try:
                    parts = line.split("Generated EIP")[1].strip().split("for issue")
                    eip_id = parts[0].strip()
                    issue_info = parts[1].strip().split("#", 1)
                    
                    # Extract issue number, removing any trailing spaces or characters
                    issue_number = issue_info[1].strip() if len(issue_info) > 1 else ""
                    if not issue_number.isdigit() and issue_number:
                        # If there are extra characters, extract just the digits
                        import re
                        match = re.search(r'(\d+)', issue_number)
                        if match:
                            issue_number = match.group(1)
                        else:
                            issue_number = "unknown"
                    
                    # Lookup the issue title from our collected titles
                    issue_title = issue_titles.get(issue_number, "Unknown Issue")
                    
                    # Make EIP ID unique by adding the issue number if it's not already there
                    if not any(c.isdigit() for c in eip_id.split('-')[-1]):
                        eip_id = f"{eip_id}-{issue_number}"
                    
                    # Generate a sample EIP content for the draft
                    eip_content = f"""---
eip: draft
title: Response to: {issue_title}
author: Kephra Agent (Auto-generated)
status: Draft
type: Standards Track
category: Core
created: {datetime.now().isoformat()}
---

## Abstract

This EIP was automatically generated in response to GitHub issue #{issue_number}: {issue_title}. 
The full specification is being developed.

## Motivation

This EIP aims to address the issues raised in GitHub issue #{issue_number}.

## Specification

The proposed solution builds upon the Ethereum protocol to ensure backward compatibility
while addressing the identified needs.

## Rationale

This approach was chosen to balance technical constraints with the needs expressed in the issue.

## Implementation

A reference implementation will be provided once the specification is finalized.
"""
                    
                    # Check if this draft EIP is already in our collection
                    if eip_id not in draft_eips:
                        draft_eips[eip_id] = {
                            "eip_data": {
                                "title": f"Response to: {issue_title}",
                                "author": "Kephra Agent (Auto-generated)",
                                "status": "Draft",
                                "type": "Standards Track",
                                "category": "Core",
                                "abstract": f"This EIP was automatically generated in response to GitHub issue #{issue_number}: {issue_title}. The full specification is being developed.",
                                "motivation": f"This EIP aims to address the issues raised in GitHub issue #{issue_number}.",
                                "specification": "The proposed solution builds upon the Ethereum protocol to ensure backward compatibility while addressing the identified needs.",
                                "rationale": "This approach was chosen to balance technical constraints with the needs expressed in the issue.",
                                "implementation": "A reference implementation will be provided once the specification is finalized.",
                                "created": datetime.now().isoformat(),
                                "full_content": eip_content
                            },
                            "status": "draft",
                            "created_at": datetime.now().isoformat(),
                            "issue_number": issue_number,
                            "issue_title": issue_title,
                            "reviews": {},
                            "simulations": {},
                            "is_generated": True
                        }
                except Exception as e:
                    logger.error(f"Error parsing EIP generation log: {e}")
        
        # If we have draft EIPs from logs, add them to generated_eips
        if draft_eips:
            generated_eips.update(draft_eips)
            real_eips_found = True
            logger.info(f"Found {len(draft_eips)} draft EIPs from logs")
        
        # Now process EIP files if the directory exists
        if eips_dir.exists():
            eip_files = list(eips_dir.glob("*.md"))
            
            # If the directory exists but has no real EIPs (or just empty README),
            # create some example EIPs for demo purposes
            if len(eip_files) == 0 or (len(eip_files) == 1 and eip_files[0].name.lower() == "readme.md"):
                if not real_eips_found:
                    logger.info("No real EIPs found in files. No mock EIPs will be displayed.")
                    # Don't create demo EIPs
                    pass
            else:
                # Process real EIP files
                for eip_file in eip_files:
                    if eip_file.name.lower() == "readme.md":
                        continue
                    
                    try:
                        # Read the EIP file
                        content = eip_file.read_text()
                        
                        # Extract basic metadata using regex patterns
                        import re
                        
                        eip_id_match = re.search(r'eip:\s*(\d+)', content)
                        title_match = re.search(r'title:\s*(.+?)(?:\n|$)', content)
                        author_match = re.search(r'author:\s*(.+?)(?:\n|$)', content)
                        status_match = re.search(r'status:\s*(.+?)(?:\n|$)', content)
                        type_match = re.search(r'type:\s*(.+?)(?:\n|$)', content)
                        
                        # Get the abstract section
                        abstract_match = re.search(r'## Abstract\s+(.+?)(?=##|\Z)', content, re.DOTALL)
                        
                        # Get other sections
                        motivation_match = re.search(r'## Motivation\s+(.+?)(?=##|\Z)', content, re.DOTALL)
                        specification_match = re.search(r'## Specification\s+(.+?)(?=##|\Z)', content, re.DOTALL)
                        rationale_match = re.search(r'## Rationale\s+(.+?)(?=##|\Z)', content, re.DOTALL)
                        implementation_match = re.search(r'## Implementation\s+(.+?)(?=##|\Z)', content, re.DOTALL)
                        
                        eip_id = f"EIP-{eip_id_match.group(1)}" if eip_id_match else eip_file.stem.upper()
                        
                        # Add to active proposals
                        generated_eips[eip_id] = {
                            "eip_data": {
                                "title": title_match.group(1).strip() if title_match else "Unknown",
                                "author": author_match.group(1).strip() if author_match else "Unknown",
                                "status": status_match.group(1).strip() if status_match else "Draft",
                                "type": type_match.group(1).strip() if type_match else "Standards Track",
                                "abstract": abstract_match.group(1).strip() if abstract_match else "No abstract",
                                "motivation": motivation_match.group(1).strip() if motivation_match else "",
                                "specification": specification_match.group(1).strip() if specification_match else "",
                                "rationale": rationale_match.group(1).strip() if rationale_match else "",
                                "implementation": implementation_match.group(1).strip() if implementation_match else "",
                                "created": datetime.now().isoformat(),
                                "full_content": content
                            },
                            "status": "draft",
                            "created_at": datetime.now().isoformat(),
                            "file_path": str(eip_file),
                            "reviews": {},
                            "simulations": {},
                            "is_file": True
                        }
                        real_eips_found = True
                    except Exception as e:
                        logger.error(f"Error parsing EIP file {eip_file}: {e}")
                
                logger.info(f"Found {len(generated_eips)} EIPs in repository")
    
    except Exception as e:
        logger.error(f"Error reading EIP repository: {e}")
    
    # If no EIPs found or can't read directory, don't use demo EIPs
    if not generated_eips:
        logger.info("No EIPs found in repository - add EIPs to the repository directory to see them here")
        # Keep empty dictionary instead of creating demo EIPs
        generated_eips = {}
    
    # Update active proposals
    active_proposals = generated_eips
    
    # Broadcast to clients
    await manager.broadcast(json.dumps({
        "type": "proposals",
        "proposals": active_proposals
    }))
    
    # Also extract active agents from logs and broadcast them
    await parse_agents()

async def parse_agents():
    """Parse active agents from logs and system state."""
    # Extract agents from logs
    agents = {}
    agent_types = {
        "Proposer": "PROPOSER",
        "Reviewer": "REVIEWER",
        "Simulator": "SIMULATOR",
        "Consensus": "CONSENSUS",
        "GitHub": "GITHUB",
        "EIP Repository": "REPOSITORY"
    }
    
    # Look for agent patterns in logs
    agent_patterns = [
        "Agent", "processing input", "initialized", "evaluating", "reviewing",
        "simulating", "generating", "analyzing", "consensus"
    ]
    
    # Check for agent initialization in logs
    for line in log_buffer:
        # First, check the exact patterns
        for agent_name_prefix, agent_type in agent_types.items():
            if f"{agent_name_prefix}" in line and ("processing input" in line or "initialized" in line):
                try:
                    # Try to extract agent name from logs
                    if "INFO - " in line:
                        agent_name = line.split("INFO - ")[1].split(" processing")[0].strip()
                        # If agent name is still not extracted properly, use the agent_name_prefix
                        if not agent_name or len(agent_name) > 50:
                            agent_name = f"{agent_name_prefix} Agent"
                        
                        # Add or update agent
                        agent_id = agent_name.lower().replace(" ", "_")
                        if agent_id not in agents:
                            agents[agent_id] = {
                                "name": agent_name,
                                "agent_type": agent_type,
                                "role": f"Process {agent_type.lower().capitalize()} tasks",
                                "status": "active",
                                "last_seen": datetime.now().isoformat()
                            }
                except Exception as e:
                    logger.error(f"Error parsing agent from log: {e}")
        
        # Then check for any agent pattern
        for pattern in agent_patterns:
            if pattern in line and "Agent" in line:
                try:
                    # Try to identify agent type
                    agent_type = None
                    for prefix, atype in agent_types.items():
                        if prefix.lower() in line.lower():
                            agent_type = atype
                            break
                    
                    if not agent_type:
                        # Default to a generic agent type
                        agent_type = "AGENT"
                    
                    # Try to extract agent name from logs
                    agent_name = None
                    if "INFO - " in line:
                        parts = line.split("INFO - ")[1].split(" ")
                        # Find the part that has "Agent" in it
                        for i, part in enumerate(parts):
                            if "Agent" in part and i > 0:
                                agent_name = " ".join(parts[i-1:i+1])
                                break
                            
                    # If agent name is still not extracted properly, use a generic name
                    if not agent_name:
                        agent_name = f"Kephra Agent ({agent_type.capitalize()})"
                    
                    # Trim the agent name if it's too long
                    if len(agent_name) > 50:
                        agent_name = agent_name[:47] + "..."
                    
                    # Add or update agent
                    agent_id = agent_name.lower().replace(" ", "_").replace(".", "_")
                    if agent_id not in agents:
                        agents[agent_id] = {
                            "name": agent_name,
                            "agent_type": agent_type,
                            "role": f"Process {agent_type.lower().capitalize()} tasks",
                            "status": "active",
                            "last_seen": datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error parsing agent pattern from log: {e}")
    
    # If no agents found from logs but the system is running, add some default agents
    if not agents and kephra_process is not None and kephra_process.poll() is None:
        agents = {
            "proposer": {
                "name": "EIP Proposer",
                "agent_type": "PROPOSER",
                "role": "Generate EIP drafts from GitHub issues",
                "status": "active",
                "last_seen": datetime.now().isoformat()
            },
            "reviewer": {
                "name": "Protocol Reviewer",
                "agent_type": "REVIEWER",
                "role": "Review EIPs for protocol compliance",
                "status": "active", 
                "last_seen": datetime.now().isoformat()
            },
            "security_reviewer": {
                "name": "Security Reviewer",
                "agent_type": "REVIEWER",
                "role": "Analyze EIPs for security implications",
                "status": "active",
                "last_seen": datetime.now().isoformat()
            },
            "simulator": {
                "name": "Protocol Simulator",
                "agent_type": "SIMULATOR",
                "role": "Simulate EIPs to test effects on network",
                "status": "active",
                "last_seen": datetime.now().isoformat()
            },
            "github_agent": {
                "name": "GitHub Issues Agent",
                "agent_type": "GITHUB",
                "role": "Monitor GitHub issues for EIP candidates",
                "status": "active",
                "last_seen": datetime.now().isoformat()
            }
        }
    
    # Broadcast agents to clients
    await manager.broadcast(json.dumps({
        "type": "agents",
        "agents": agents
    }))

def create_demo_eips():
    """Create demo EIPs for demonstration purposes."""
    # Return empty dict instead of creating mock EIPs
    return {}

def open_browser():
    """Open the browser to the dashboard URL."""
    try:
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        logger.error(f"Error opening browser: {e}")

@app.on_event("startup")
async def startup_event():
    # Schedule browser opening without asyncio
    Thread(target=lambda: time.sleep(1.5) or open_browser(), daemon=True).start()
    
    # Start periodic refresh tasks
    asyncio.create_task(periodic_refresh())
    
    # Generate protocol insights
    protocol_insights = await generate_protocol_insights()
    if protocol_insights and protocol_insights.snapshot:
        await broadcast_message({
            "type": "protocol_insights",
            "health_scores": {
                "network": protocol_insights.snapshot.network_health_score,
                "economic": protocol_insights.snapshot.economic_health_score,
                "security": protocol_insights.snapshot.security_health_score or 0.0
            },
            "alerts_count": len(protocol_insights.alerts),
            "recommendations_count": len(protocol_insights.recommendations)
        })

async def periodic_refresh():
    """Periodically refresh GitHub issues and proposals."""
    while True:
        try:
            # Wait for 5 minutes
            await asyncio.sleep(300)
            
            # Refresh GitHub issues
            logger.info("Refreshing GitHub issues...")
            await parse_github_issues()
            
            # Refresh EIP proposals
            logger.info("Refreshing EIP proposals...")
            await parse_proposals()
            
        except asyncio.CancelledError:
            # Clean exit on cancellation
            break
        except Exception as e:
            logger.error(f"Error in periodic refresh: {e}")
            # Don't fail, just log and try again next time

async def generate_protocol_insights():
    logger.info("Generating protocol insights from metrics analyzer")
    try:
        # Initialize data manager and metrics analyzer
        data_manager = ProtocolDataManager()
        analyzer = MetricsAnalyzer(data_manager)
        
        # Generate insight report
        report = analyzer.generate_insight_report()
        
        # Log the summary
        if report.summary:
            logger.info(f"Protocol Insight Summary: {report.summary}")
        
        # Log health scores
        if report.snapshot:
            logger.info(f"Network Health: {report.snapshot.network_health_score:.2f}")
            logger.info(f"Economic Health: {report.snapshot.economic_health_score:.2f}")
            if report.snapshot.security_health_score:
                logger.info(f"Security Health: {report.snapshot.security_health_score:.2f}")
        
        # Log alerts
        if report.alerts:
            logger.info(f"Detected {len(report.alerts)} protocol alerts")
            for alert in report.alerts[:3]:  # Log first 3 alerts
                logger.info(f"Alert: {alert.severity} - {alert.description}")
        
        # Log recommendations
        if report.recommendations:
            logger.info(f"Generated {len(report.recommendations)} protocol recommendations")
            for rec in report.recommendations[:3]:  # Log first 3 recommendations
                logger.info(f"Recommendation: {rec.title} (Priority: {rec.priority})")
                logger.info(f"Rationale: {rec.rationale}")
        
        return report
    except Exception as e:
        logger.error(f"Error generating protocol insights: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Create the templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000) 