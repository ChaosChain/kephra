import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import time as python_time
import threading
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="Kephra - Full Ethereum Governance Workflow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add a session state for auto-navigation
if 'auto_navigation' not in st.session_state:
    st.session_state.auto_navigation = True  # Set to True by default
    st.session_state.current_workflow_stage = 0
    st.session_state.last_stage_change = python_time.time()
    st.session_state.transition_message = ""

# Define workflow stages as a list for easier navigation
WORKFLOW_STAGES = [
    "1️⃣ Issue Identification", 
    "2️⃣ EIP Creation", 
    "3️⃣ Implementation & Testing", 
    "4️⃣ Review & Evaluation", 
    "5️⃣ Consensus Building", 
    "6️⃣ Complete System Flow"
]

# Define transition messages between workflow stages
TRANSITION_MESSAGES = [
    "Moving to EIP creation phase: The Proposer Agent is now formalizing the identified issue into a proper EIP specification.",
    "Moving to implementation and testing: The Simulator Agent is now implementing the EIP and creating test cases.",
    "Moving to review and evaluation: The Reviewer Agent is now analyzing the implementation for correctness and quality.",
    "Moving to consensus building: The Consensus Agent is now aggregating reviews to reach a final determination.",
    "Moving to complete system overview: Showing how all agents work together in the Kephra ecosystem.",
    "Returning to issue identification: Restarting the workflow demonstration from the beginning."
]

# Add a function to explain the current workflow stage context
def get_stage_context(stage_index):
    contexts = [
        "In this stage, the Proposer Agent continuously monitors Ethereum repositories, forums, and network metrics to identify potential improvement opportunities. It analyzes issues for impact, feasibility, and alignment with Ethereum's goals.",
        
        "In this stage, the Proposer Agent creates a formal Ethereum Improvement Proposal (EIP) with detailed technical specifications, rationale, and backward compatibility considerations.",
        
        "In this stage, the Simulator Agent implements the proposed changes in actual code and conducts comprehensive testing to verify functionality, security, and performance improvements.",
        
        "In this stage, the Reviewer Agent performs thorough analysis of the EIP and implementation against standardized criteria for technical correctness, standards compliance, and value alignment.",
        
        "In this stage, the Consensus Agent aggregates evaluations from multiple reviewers, resolves conflicting opinions, and builds a final determination with reputation-weighted consensus.",
        
        "This overview shows the complete Kephra workflow and how all agents interact throughout the Ethereum governance process."
    ]
    
    return contexts[stage_index]

# Custom CSS
st.markdown("""
<style>
/* General styling */
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}

/* Agent-specific background colors */
.proposer-bg {
    background: linear-gradient(135deg, rgba(100,149,237,0.1) 0%, rgba(100,149,237,0.2) 100%);
    border-left: 4px solid #6495ED;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.reviewer-bg {
    background: linear-gradient(135deg, rgba(50,205,50,0.1) 0%, rgba(50,205,50,0.2) 100%);
    border-left: 4px solid #32CD32;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.simulator-bg {
    background: linear-gradient(135deg, rgba(255,165,0,0.1) 0%, rgba(255,165,0,0.2) 100%);
    border-left: 4px solid #FFA500;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.consensus-bg {
    background: linear-gradient(135deg, rgba(138,43,226,0.1) 0%, rgba(138,43,226,0.2) 100%);
    border-left: 4px solid #8A2BE2;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.agent-bg {
    background: linear-gradient(135deg, rgba(128,128,128,0.1) 0%, rgba(128,128,128,0.2) 100%);
    border-left: 4px solid #808080;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

/* Agent activity containers */
.agent-activity-container {
    margin-top: 20px;
    margin-bottom: 20px;
    padding: 10px;
    border-radius: 5px;
}

/* Agent cards */
.agent-card {
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.agent-card h3 {
    margin-top: 0;
    margin-bottom: 10px;
}

/* Timeline styling */
.timeline-container {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    margin-bottom: 30px;
    position: relative;
}

.timeline-container:after {
    content: '';
    position: absolute;
    width: 100%;
    height: 3px;
    background-color: #ddd;
    top: 50%;
    left: 0;
    z-index: -1;
}

.timeline-step {
    background-color: white;
    padding: 5px 15px;
    border-radius: 20px;
    border: 2px solid #ddd;
    position: relative;
    z-index: 1;
    cursor: pointer;
    transition: all 0.3s;
}

.timeline-step.active {
    background-color: #4CAF50;
    color: white;
    border-color: #4CAF50;
    font-weight: bold;
}

.timeline-step.completed {
    background-color: #8bc34a;
    color: white;
    border-color: #8bc34a;
}

/* Data frames */
.dataframe-container {
    margin: 20px 0;
    overflow-x: auto;
}

.kpi-card {
    background: white;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    padding: 15px;
    text-align: center;
    margin-bottom: 20px;
}

.kpi-card h3 {
    margin-top: 0;
    color: #555;
    font-size: 16px;
}

.kpi-card p {
    font-size: 24px;
    font-weight: bold;
    margin: 10px 0 0 0;
}

/* EIP document styling */
.eip-document {
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 20px;
    font-family: monospace;
    margin-bottom: 20px;
}

.eip-document h4 {
    margin-top: 0;
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
}

/* Code block styling */
pre.code-block {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    margin-bottom: 20px;
}

/* Evaluation metrics styling */
.score-container {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.score-label {
    min-width: 200px;
}

.score-bar {
    height: 20px;
    background-color: #4CAF50;
    border-radius: 5px;
    margin-right: 10px;
}

.score-value {
    font-weight: bold;
}

/* Button styling */
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 24px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 4px;
}

.stButton>button:hover {
    background-color: #45a049;
}
</style>
""", unsafe_allow_html=True)

# Page title
st.markdown('<h1 class="main-header">Kephra: End-to-End Ethereum Governance Workflow</h1>', unsafe_allow_html=True)
st.markdown("""
This demo showcases the complete workflow of Kephra's autonomous agent system - from identifying issues in Ethereum repositories,
to formal EIP creation, implementation, testing, review and consensus building.
""")

# Sidebar navigation
st.sidebar.title("Workflow Navigation")

# Add auto-navigation toggle
auto_nav = st.sidebar.checkbox("Enable Automatic Navigation", 
                               value=st.session_state.auto_navigation,
                               help="Automatically cycle through all workflow stages")

# Update session state
if auto_nav != st.session_state.auto_navigation:
    st.session_state.auto_navigation = auto_nav
    st.session_state.last_stage_change = python_time.time()
    st.session_state.transition_message = ""

# Handle auto-navigation logic
if st.session_state.auto_navigation:
    # Time to spend on each stage (in seconds)
    STAGE_DURATION = 45  # Increased duration to give users more time to read content
    
    current_time = python_time.time()
    elapsed_time = current_time - st.session_state.last_stage_change
    
    if elapsed_time > STAGE_DURATION:
        # Store transition message
        st.session_state.transition_message = TRANSITION_MESSAGES[st.session_state.current_workflow_stage]
        
        # Move to next stage
        st.session_state.current_workflow_stage = (st.session_state.current_workflow_stage + 1) % len(WORKFLOW_STAGES)
        st.session_state.last_stage_change = current_time
        st.rerun()
    
    # Display timer
    remaining_time = STAGE_DURATION - elapsed_time
    st.sidebar.progress(1 - (remaining_time / STAGE_DURATION))
    st.sidebar.text(f"Next stage in: {int(remaining_time)} seconds")
    
    # Set workflow stage based on current index
    workflow_stage = WORKFLOW_STAGES[st.session_state.current_workflow_stage]
    st.sidebar.radio(
        "Current workflow stage:",
        WORKFLOW_STAGES,
        index=st.session_state.current_workflow_stage,
        key="workflow_stage_radio",
        disabled=True
    )
else:
    # Manual selection
    workflow_stage_index = WORKFLOW_STAGES.index(workflow_stage) if 'workflow_stage' in locals() else 0
    workflow_stage = st.sidebar.radio(
        "Select workflow stage:",
        WORKFLOW_STAGES,
        index=workflow_stage_index
    )
    st.session_state.current_workflow_stage = WORKFLOW_STAGES.index(workflow_stage)
    st.session_state.transition_message = ""  # Clear transition message on manual navigation

# Display transition message if present
if st.session_state.transition_message:
    st.markdown(f'<div class="transition-message">🔄 {st.session_state.transition_message}</div>', unsafe_allow_html=True)

# Display current stage context
current_context = get_stage_context(st.session_state.current_workflow_stage)
st.markdown(f'<div class="stage-context">{current_context}</div>', unsafe_allow_html=True)

# Workflow Timeline Navigator
def display_workflow_timeline():
    """Display an interactive timeline of the workflow stages"""
    
    st.markdown("### Workflow Timeline")
    
    # Create timeline container
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    for i, stage_name in enumerate(WORKFLOW_STAGES):
        # Determine stage status
        current_index = WORKFLOW_STAGES.index(workflow_stage)
        
        if i < current_index:
            status_class = "completed"
        elif i == current_index:
            status_class = "active"
        else:
            status_class = ""
        
        # Display timeline step
        step_label = stage_name.split('️⃣ ')[1] if '️⃣ ' in stage_name else stage_name
        st.markdown(f'<div class="timeline-step {status_class}">{step_label}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Add this call right after displaying the stage context
display_workflow_timeline()

# Add a function to consistently display EIP documents in a styled format
def display_eip_document(title, content):
    """Display an EIP document with consistent styling"""
    st.markdown(f'<div class="eip-document"><h4>{title}</h4>{content}</div>', unsafe_allow_html=True)

# Add a function to display code with syntax highlighting
def display_code(code, language="python"):
    """Display code with consistent styling"""
    st.markdown(f'<pre class="code-block">{code}</pre>', unsafe_allow_html=True)

# Add a KPI metrics display function
def display_kpi_metrics(metrics):
    """Display a set of KPI metrics in card format
    metrics should be a list of dicts with 'title' and 'value' keys
    """
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{metric['title']}</h3>
                <p>{metric['value']}</p>
            </div>
            """, unsafe_allow_html=True)

# Add a function to display evaluation scores
def display_score_metrics(scores):
    """Display a set of evaluation scores with progress bars
    scores should be a dict where keys are criteria and values are scores (0-100)
    """
    for criterion, score in scores.items():
        # Calculate width percentage
        width = score
        
        st.markdown(f"""
        <div class="score-container">
            <div class="score-label">{criterion}</div>
            <div class="score-bar" style="width: {width}%;"></div>
            <div class="score-value">{score}%</div>
        </div>
        """, unsafe_allow_html=True)

# Sidebar MCP integration toggle
st.sidebar.markdown("---")
use_mcp = st.sidebar.checkbox("Enable MCP Integration", value=True,
                             help="Toggle Model Context Protocol integration for enhanced agent capabilities")

# Sidebar agent configuration
st.sidebar.markdown("---")
st.sidebar.subheader("Agent Configuration")
proposer_model = st.sidebar.selectbox("Proposer Agent Model", ["gpt-4o", "claude-3-opus", "claude-3-sonnet"])
reviewer_model = st.sidebar.selectbox("Reviewer Agent Model", ["claude-3-opus", "gpt-4o", "claude-3-sonnet"])
simulator_model = st.sidebar.selectbox("Simulator Agent Model", ["claude-3-sonnet", "gpt-4o", "claude-3-haiku"])
consensus_model = st.sidebar.selectbox("Consensus Agent Model", ["gpt-4o", "claude-3-opus", "claude-3-sonnet"])

# Sample EIPs for demo
sample_eips = {
    "EIP-1559": {
        "title": "Fee Market Change for ETH 1.0 Chain",
        "description": "A transaction pricing mechanism that includes fixed-per-block network fee that is burned and dynamically expands/contracts block sizes to deal with transient congestion.",
        "type": "Core",
        "status": "Final",
        "complexity": "High"
    },
    "EIP-4844": {
        "title": "Shard Blob Transactions",
        "description": "A new transaction format for 'blob-carrying transactions' which contain a large amount of data that cannot be accessed by EVM execution, but whose commitment can be accessed.",
        "type": "Core",
        "status": "Final",
        "complexity": "High"
    },
    "EIP-4337": {
        "title": "Account Abstraction",
        "description": "A method for allowing user operations to be passed and included on-chain while paying for gas without requiring any consensus-layer protocol changes.",
        "type": "ERC",
        "status": "Review",
        "complexity": "Medium"
    }
}

# Add the helper function for agent activity display
def display_agent_activities(agent_type, activities, auto_run=False):
    """Display a list of agent activities with animated progress"""
    
    if agent_type == "proposer":
        emoji = "📝"
        color = "proposer-bg"
    elif agent_type == "reviewer":
        emoji = "🔍"
        color = "reviewer-bg"
    elif agent_type == "simulator":
        emoji = "🧪"
        color = "simulator-bg"
    elif agent_type == "consensus":
        emoji = "🤝"
        color = "consensus-bg"
    else:
        emoji = "🤖"
        color = "agent-bg"
    
    st.markdown(f'<div class="{color} agent-activity-container">', unsafe_allow_html=True)
    st.markdown(f"### {emoji} Agent Activity Log")
    
    activity_placeholder = st.empty()
    
    if auto_run or st.session_state.get('auto_navigate', True):
        activities_text = ""
        
        for i, activity in enumerate(activities):
            activities_text += f"{'✓' if i < len(activities)-1 else '⟳'} {activity}\n"
            activity_placeholder.markdown(f"```\n{activities_text}\n```")
            if i < len(activities)-1:  # Don't sleep after the last activity
                time.sleep(0.5)
    else:
        # Just show all activities without animation
        activities_text = "\n".join([f"✓ {activity}" for activity in activities])
        activity_placeholder.markdown(f"```\n{activities_text}\n```")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Add agent role explanation function
def explain_agent_role(agent_type):
    """Return a detailed explanation of an agent's role"""
    
    if agent_type == "proposer":
        title = "📝 Proposer Agent"
        description = """
        Monitors Ethereum repositories, forums, and network metrics to identify improvement opportunities and draft formal EIPs.
        
        **Primary Role**: Identify issues and create formal EIP specifications
        
        **Key Capabilities**:
        - Repository and forum monitoring
        - Issue prioritization and analysis
        - Formal EIP specification creation
        - Standards compliance validation
        
        **Technical Foundation**: Natural language processing, issue classification, and formal specification generation
        """
        css_class = "proposer-bg"
    
    elif agent_type == "reviewer":
        title = "🔍 Reviewer Agent"
        description = """
        Evaluates EIPs for technical correctness, standards compliance, and implementation quality.
        
        **Primary Role**: Provide objective technical assessment of proposals
        
        **Key Capabilities**:
        - Technical correctness evaluation
        - Standards compliance checking
        - Security vulnerability identification
        - Implementation quality assessment
        - Recommendations for improvements
        
        **Technical Foundation**: Static analysis, formal verification methods, and standards compliance frameworks
        """
        css_class = "reviewer-bg"
    
    elif agent_type == "simulator":
        title = "🧪 Simulator Agent"
        description = """
        Implements reference code and creates test environments to validate EIP functionality and performance.
        
        **Primary Role**: Create and test reference implementations
        
        **Key Capabilities**:
        - Reference implementation creation
        - Test case generation
        - Performance benchmarking
        - Edge case identification
        - Network impact simulation
        
        **Technical Foundation**: Code generation, test automation, and simulation modeling
        """
        css_class = "simulator-bg"
    
    elif agent_type == "consensus":
        title = "🤝 Consensus Agent"
        description = """
        Aggregates reviewer feedback, mediates disagreements, and determines final proposal status.
        
        **Primary Role**: Determine consensus from multiple reviewer assessments
        
        **Key Capabilities**:
        - Review aggregation and normalization
        - Weighted consensus calculation
        - Disagreement mediation
        - Expert opinion coordination
        - Final determination publishing
        
        **Technical Foundation**: Reputation-weighted voting algorithms and formal consensus protocols
        """
        css_class = "consensus-bg"
    
    else:
        title = "🤖 Agent"
        description = "General Kephra agent"
        css_class = "agent-bg"
    
    return f"""
    <div class="{css_class} agent-card">
        <h3>{title}</h3>
        {description}
    </div>
    """

# Define workflow stage display functions
def show_issue_identification():
    """Display the Issue Identification stage of the workflow"""
    st.markdown("## 📝 Issue Identification Stage")
    
    # Explain agent's role
    st.markdown(explain_agent_role("proposer"), unsafe_allow_html=True)
    
    # Create columns for metrics and visualization
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display agent activities
        proposer_activities = [
            "Monitoring Ethereum GitHub repositories for open issues...",
            "Scanning Ethereum Magicians forum for discussion threads...",
            "Analyzing network metrics for performance bottlenecks...",
            "Prioritizing issues based on impact and community interest...",
            "Identified high-priority issue: 'Transaction fee volatility during network congestion'",
            "Extracting key requirements and constraints...",
            "Validating issue against historical data...",
            "Issue validated with high confidence (94%)"
        ]
        
        display_agent_activities("proposer", proposer_activities)
        
        # Display issue details
        st.markdown("### 🔍 Issue Details")
        st.markdown("""
        <div class="proposer-bg" style="padding: 15px; border-radius: 5px;">
            <h4>Transaction Fee Volatility</h4>
            <p><strong>Source:</strong> Multiple GitHub issues, Ethereum Magicians forum discussions</p>
            <p><strong>Impact:</strong> High - Affects all network users during congestion periods</p>
            <p><strong>Description:</strong> During periods of network congestion, gas prices become highly volatile and unpredictable, causing poor user experience and economic inefficiency in the network.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Display KPI metrics
        kpi_metrics = [
            {"title": "Issues Analyzed", "value": "325"},
            {"title": "Priority Score", "value": "8.7/10"},
            {"title": "Community Interest", "value": "High"}
        ]
        display_kpi_metrics(kpi_metrics)
        
        # Display a simple gas price volatility chart
        st.markdown("### Gas Price Volatility")
        
        # Generate mock data for gas price volatility
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        base_gas_price = 50
        volatility = np.random.normal(0, 15, 30)
        spikes = np.zeros(30)
        spikes[[5, 12, 18, 25]] = [80, 100, 70, 90]  # Add some congestion spikes
        gas_prices = base_gas_price + volatility + spikes
        
        df = pd.DataFrame({
            'Date': dates,
            'Gas Price (Gwei)': np.maximum(gas_prices, 10)  # Ensure no negative prices
        })
        
        # Plot the data
        fig = px.line(df, x='Date', y='Gas Price (Gwei)', title='Gas Price Volatility')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def show_eip_creation():
    """Display the EIP Creation stage of the workflow"""
    st.markdown("## 📄 EIP Creation Stage")
    
    # Explain agent's role
    st.markdown(explain_agent_role("proposer"), unsafe_allow_html=True)
    
    # Create columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display agent activities
        proposer_activities = [
            "Gathering technical requirements from issue analysis...",
            "Researching existing solutions and approaches...",
            "Identifying most suitable EIP type for this proposal...",
            "Drafting EIP preamble with metadata...",
            "Generating technical specification...",
            "Adding rationale and backward compatibility considerations...",
            "Performing self-review against EIP-1 format requirements...",
            "Finalizing draft proposal: EIP-1559 Fee Market Change"
        ]
        
        display_agent_activities("proposer", proposer_activities)
        
        # Display EIP document
        eip_content = """
        <p><strong>EIP:</strong> 1559</p>
        <p><strong>Title:</strong> Fee Market Change for ETH 1.0 Chain</p>
        <p><strong>Author:</strong> Vitalik Buterin, Eric Conner, Rick Dudley, Matthew Slipper, Ian Norden</p>
        <p><strong>Status:</strong> Draft</p>
        <p><strong>Type:</strong> Core</p>
        <p><strong>Created:</strong> 2019-04-13</p>
        
        <h5>Abstract</h5>
        <p>A transaction pricing mechanism that includes fixed-per-block network fee that is burned and dynamically expands/contracts block sizes to deal with transient congestion.</p>
        
        <h5>Motivation</h5>
        <p>The current "first price auction" fee market in Ethereum leads to fee price unpredictability and inefficient fee estimation strategies, resulting in many users paying significantly more in transaction fees than required. This EIP aims to stabilize transaction fee prices, improving the user experience and economic efficiency of Ethereum's fee market.</p>
        
        <h5>Specification</h5>
        <p>There is a base fee per gas in protocol, which can move up or down by a maximum of 1/8 in each block. The base fee per gas is adjusted to target an average gas usage of 10M per block.</p>
        <p>Transactions now specify a fee cap, which is the maximum total fee per gas they're willing to pay. They also specify a priority fee per gas, which is the maximum amount above the base fee they're willing to pay.</p>
        
        <h5>Backwards Compatibility</h5>
        <p>This EIP requires a scheduled network upgrade, as it introduces changes to the block and transaction structure.</p>
        """
        display_eip_document("EIP-1559: Fee Market Change for ETH 1.0 Chain", eip_content)
    
    with col2:
        # Display KPI metrics
        kpi_metrics = [
            {"title": "Format Compliance", "value": "96%"},
            {"title": "Specification Clarity", "value": "8.8/10"},
            {"title": "Completion Time", "value": "3.2 hrs"}
        ]
        display_kpi_metrics(kpi_metrics)
        
        # Display format checks
        st.markdown("### EIP Format Checks")
        
        # Create a mock format check results display
        format_scores = {
            "Preamble Completeness": 100,
            "Abstract Quality": 95,
            "Specification Detail": 92,
            "Rationale Clarity": 85,
            "Backward Compatibility": 90
        }
        
        display_score_metrics(format_scores)
        
        # Show a small visualization
        st.markdown("### Expected Impact on Fee Volatility")
        
        # Create mock data for before/after comparison
        df_before = pd.DataFrame({
            'Time': range(1, 31),
            'Gas Price': np.maximum(50 + np.random.normal(0, 20, 30) + np.array([0]*20 + [100, 120, 90, 80, 70, 60, 50, 40, 30, 20]), 10)
        })
        
        df_after = pd.DataFrame({
            'Time': range(1, 31),
            'Gas Price': np.maximum(50 + np.random.normal(0, 5, 30) + np.array([0]*20 + [20, 35, 40, 38, 35, 30, 25, 22, 20, 18]), 10)
        })
        
        fig = make_subplots(rows=2, cols=1, subplot_titles=("Current Fee Market", "EIP-1559 Fee Market"))
        
        fig.add_trace(
            go.Scatter(x=df_before['Time'], y=df_before['Gas Price'], mode='lines', name='Before'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df_after['Time'], y=df_after['Gas Price'], mode='lines', name='After'),
            row=2, col=1
        )
        
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def show_implementation_testing():
    """Display the Implementation & Testing stage of the workflow"""
    st.markdown("## 🧪 Implementation & Testing Stage")
    
    # Explain agent's role
    st.markdown(explain_agent_role("simulator"), unsafe_allow_html=True)
    
    # Create columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display agent activities
        simulator_activities = [
            "Analyzing EIP-1559 technical specification...",
            "Breaking down implementation requirements...",
            "Generating reference implementation for Geth client...",
            "Creating unit tests for base fee adjustment algorithm...",
            "Developing integration tests for transaction processing...",
            "Simulating network under varying load conditions...",
            "Analyzing performance impact under high congestion...",
            "Finalizing implementation with test coverage: 94%"
        ]
        
        display_agent_activities("simulator", simulator_activities)
        
        # Display implementation code
        implementation_code = """
// BASEFEE opcode implementation
func opBaseFee(pc *uint64, interpreter *EVMInterpreter, scope *ScopeContext) ([]byte, error) {
	baseFee := interpreter.evm.Context.BaseFee
	if baseFee == nil {
		// Return 0 if baseFee is nil
		scope.Stack.push(new(uint256.Int))
		return nil, nil
	}
	scope.Stack.push(uint256.NewInt(baseFee.ToBig()))
	return nil, nil
}

// Calculate new base fee for next block
func CalcBaseFee(parent *types.Header, gasLimit uint64) *big.Int {
	// If the parent gas used is the same as the target, the base fee remains unchanged
	if parent.GasUsed == parent.GasLimit/2 {
		return new(big.Int).Set(parent.BaseFee)
	}

	// Calculate gas used delta from target
	var gasUsedDelta *big.Int
	if parent.GasUsed > parent.GasLimit/2 {
		gasUsedDelta = new(big.Int).SetUint64(parent.GasUsed - parent.GasLimit/2)
	} else {
		gasUsedDelta = new(big.Int).SetUint64(parent.GasLimit/2 - parent.GasUsed)
	}

	// Calculate base fee adjustment (parentBaseFee * gasUsedDelta / gasLimit / 8)
	baseFeeDelta := new(big.Int).Mul(parent.BaseFee, gasUsedDelta)
	baseFeeDelta.Div(baseFeeDelta, new(big.Int).SetUint64(parent.GasLimit))
	baseFeeDelta.Div(baseFeeDelta, big.NewInt(8))

	// If gas used is greater than target, increase base fee
	if parent.GasUsed > parent.GasLimit/2 {
		return new(big.Int).Add(parent.BaseFee, baseFeeDelta)
	}
	// Otherwise decrease it
	return new(big.Int).Sub(parent.BaseFee, baseFeeDelta)
}
"""
        display_code(implementation_code, "go")
    
    with col2:
        # Display KPI metrics
        kpi_metrics = [
            {"title": "Test Coverage", "value": "94%"},
            {"title": "Performance Impact", "value": "+2.3%"},
            {"title": "Integration Tests", "value": "18"}
        ]
        display_kpi_metrics(kpi_metrics)
        
        # Display test results
        st.markdown("### Test Results")
        
        # Create mock test results
        test_results = pd.DataFrame({
            'Test Type': ['Unit Tests', 'Integration Tests', 'Performance Tests', 'Fuzz Tests'],
            'Passed': [42, 16, 8, 12],
            'Failed': [0, 0, 0, 0],
            'Skipped': [2, 2, 0, 1]
        })
        
        fig = px.bar(test_results, x='Test Type', y=['Passed', 'Failed', 'Skipped'], 
                    title='Test Suite Results', barmode='stack')
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display performance comparison
        st.markdown("### Performance Analysis")
        
        # Create comparison data for before/after implementation
        perf_data = pd.DataFrame({
            'Metric': ['Block Processing Time', 'Transaction Throughput', 'Memory Usage', 'Network Bandwidth'],
            'Before (ms)': [120, 1500, 250, 85],
            'After (ms)': [123, 1450, 260, 88],
            'Change (%)': ['+2.5%', '-3.3%', '+4.0%', '+3.5%']
        })
        
        st.table(perf_data)
        
        # Simulation results
        st.markdown("### Simulation Results")
        st.markdown("""
        <div class="simulator-bg" style="padding: 15px; border-radius: 5px;">
            <p><strong>Findings:</strong></p>
            <ul>
                <li>Base fee successfully adjusts to target 50% block utilization</li>
                <li>Fee volatility reduced by ~87% during congestion events</li>
                <li>Implementation successfully handles all edge cases in test suite</li>
                <li>No negative impact observed on chain reorganizations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_review_evaluation():
    """Display the Review & Evaluation stage of the workflow"""
    st.markdown("## 🔍 Review & Evaluation Stage")
    
    # Explain agent's role
    st.markdown(explain_agent_role("reviewer"), unsafe_allow_html=True)
    
    # Create columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display agent activities
        reviewer_activities = [
            "Loading EIP-1559 specification and implementation...",
            "Checking format compliance with EIP-1 standards...",
            "Verifying technical correctness of the specification...",
            "Analyzing implementation against specification...",
            "Checking for security implications and edge cases...",
            "Evaluating backward compatibility considerations...",
            "Assessing value alignment with Ethereum principles...",
            "Generating comprehensive review with recommendations"
        ]
        
        display_agent_activities("reviewer", reviewer_activities)
        
        # Display review summary
        st.markdown("### 📋 Review Summary")
        st.markdown("""
        <div class="reviewer-bg" style="padding: 15px; border-radius: 5px;">
            <h4>Technical Review of EIP-1559</h4>
            
            <p><strong>Overall Assessment:</strong> The EIP is technically sound and well-specified. The implementation correctly follows the specification and passes all test cases.</p>
            
            <p><strong>Strengths:</strong></p>
            <ul>
                <li>Clear motivation and problem statement</li>
                <li>Detailed specification with precise formulas</li>
                <li>Thorough test coverage for various network conditions</li>
                <li>Well-considered backward compatibility approach</li>
            </ul>
            
            <p><strong>Areas for Improvement:</strong></p>
            <ul>
                <li>More detailed analysis of gas price floor behavior needed</li>
                <li>Consider adding more explicit consensus tests</li>
                <li>Expanded documentation on client implementation details</li>
            </ul>
            
            <p><strong>Recommendation:</strong> The proposal is ready to advance to the next phase with minor revisions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Display evaluation scores
        st.markdown("### Evaluation Scores")
        
        review_scores = {
            "Technical Correctness": 92,
            "Standards Compliance": 95,
            "Security Implications": 88,
            "Implementation Quality": 90,
            "Value Alignment": 94,
            "Overall Score": 91
        }
        
        display_score_metrics(review_scores)
        
        # Display security assessment
        st.markdown("### Security Assessment")
        
        security_data = pd.DataFrame({
            'Category': ['Critical', 'High', 'Medium', 'Low', 'Informational'],
            'Issues': [0, 0, 1, 2, 3]
        })
        
        fig = px.bar(security_data, x='Category', y='Issues', 
                    title='Security Issues by Severity',
                    color='Issues',
                    color_continuous_scale=px.colors.sequential.Reds)
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display recommendation
        st.markdown("### Reviewer Recommendation")
        
        recommendation_options = ["Approve", "Approve with Minor Revisions", "Needs Major Revisions", "Reject"]
        recommendation = recommendation_options[1]  # "Approve with Minor Revisions"
        
        # Create gauge chart for recommendation
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = review_scores["Overall Score"],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Rating"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 60], 'color': "red"},
                    {'range': [60, 75], 'color': "orange"},
                    {'range': [75, 85], 'color': "yellow"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"**Recommendation: {recommendation}**")

def show_consensus_building():
    """Display the Consensus Building stage of the workflow"""
    st.markdown("## 🤝 Consensus Building Stage")
    
    # Explain agent's role
    st.markdown(explain_agent_role("consensus"), unsafe_allow_html=True)
    
    # Create columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display agent activities
        consensus_activities = [
            "Collecting reviews from multiple reviewers...",
            "Normalizing evaluation scores across reviewers...",
            "Identifying areas of consensus and disagreement...",
            "Weighing reviewer feedback by reputation and expertise...",
            "Resolving conflicting opinions on gas price floor...",
            "Aggregating final recommendations and scores...",
            "Determining overall consensus status...",
            "Finalizing determination: Ready for Last Call"
        ]
        
        display_agent_activities("consensus", consensus_activities)
        
        # Display consensus summary
        st.markdown("### 📊 Consensus Summary")
        st.markdown("""
        <div class="consensus-bg" style="padding: 15px; border-radius: 5px;">
            <h4>EIP-1559 Consensus Determination</h4>
            
            <p><strong>Overall Status:</strong> Ready for Last Call</p>
            
            <p><strong>Consensus Highlights:</strong></p>
            <ul>
                <li>Strong agreement on technical approach (4/5 reviewers)</li>
                <li>Universal support for addressing fee market volatility</li>
                <li>Minor disagreements on implementation details resolved</li>
                <li>Security considerations adequately addressed</li>
            </ul>
            
            <p><strong>Community Sentiment:</strong> Strongly positive with minor concerns from miners</p>
            
            <p><strong>Next Steps:</strong> Move to Last Call status with suggested minor revisions implemented.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Display aggregated review scores
        st.markdown("### Aggregated Review Scores")
        
        # Create a chart showing scores from multiple reviewers
        reviewer_data = pd.DataFrame({
            'Criteria': ['Technical Correctness', 'Standards Compliance', 'Security Implications', 'Implementation Quality', 'Value Alignment'],
            'Core Dev A': [92, 95, 88, 90, 94],
            'Core Dev B': [90, 97, 85, 88, 92],
            'Security Expert': [88, 90, 95, 85, 90],
            'Client Dev': [95, 92, 87, 96, 91],
            'Weighted Average': [91, 94, 89, 90, 92]
        })
        
        # Melt the DataFrame for easier plotting
        reviewer_data_melted = pd.melt(reviewer_data, id_vars=['Criteria'], var_name='Reviewer', value_name='Score')
        
        # Create the chart
        fig = px.line(reviewer_data_melted, x='Criteria', y='Score', color='Reviewer', 
                     title='Review Scores by Reviewer',
                     markers=True)
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display reviewer agreement
        st.markdown("### Reviewer Agreement Analysis")
        
        # Create agreement heatmap
        agreement_data = np.array([
            [1.0, 0.9, 0.8, 0.85, 0.92],
            [0.9, 1.0, 0.75, 0.88, 0.9],
            [0.8, 0.75, 1.0, 0.78, 0.85],
            [0.85, 0.88, 0.78, 1.0, 0.89],
            [0.92, 0.9, 0.85, 0.89, 1.0]
        ])
        
        reviewers = ['Core Dev A', 'Core Dev B', 'Security Expert', 'Client Dev', 'Consensus Agent']
        
        fig = px.imshow(agreement_data, x=reviewers, y=reviewers,
                       color_continuous_scale='Viridis',
                       title='Reviewer Agreement Matrix')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display final determination
        st.markdown("### Final Determination")
        st.markdown("""
        <div style="background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center;">
            <h3 style="margin: 0;">READY FOR LAST CALL</h3>
            <p style="margin: 5px 0 0 0;">Consensus Achieved: 90%</p>
        </div>
        """, unsafe_allow_html=True)

def show_complete_flow():
    """Display the Complete System Flow of the workflow"""
    st.markdown("## 🔄 Complete Kephra Workflow Overview")
    
    # Create a diagram explaining the full workflow
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h3>End-to-End Ethereum Governance Process</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Display the workflow diagram
    workflow_fig = go.Figure()
    
    stages = ['Issue Identification', 'EIP Creation', 'Implementation & Testing', 'Review & Evaluation', 'Consensus Building', 'Implementation']
    x_positions = [0, 1, 2, 3, 4, 5]
    y_positions = [0, 0, 0, 0, 0, 0]
    
    # Add nodes
    workflow_fig.add_trace(go.Scatter(
        x=x_positions,
        y=y_positions,
        mode='markers+text',
        marker=dict(size=30, color=['#6495ED', '#6495ED', '#FFA500', '#32CD32', '#8A2BE2', '#4682B4']),
        text=stages,
        textposition="bottom center"
    ))
    
    # Add edges (connections between nodes)
    for i in range(len(x_positions)-1):
        workflow_fig.add_shape(
            type="line",
            x0=x_positions[i],
            y0=y_positions[i],
            x1=x_positions[i+1],
            y1=y_positions[i+1],
            line=dict(width=2, color="gray"),
        )
    
    # Add agent labels above the nodes
    agent_labels = ['Proposer Agent', 'Proposer Agent', 'Simulator Agent', 'Reviewer Agent', 'Consensus Agent', '']
    
    for i in range(len(x_positions)-1):  # Skip the last node which has no agent
        workflow_fig.add_annotation(
            x=x_positions[i],
            y=y_positions[i] + 0.1,
            text=agent_labels[i],
            showarrow=False,
            yshift=15
        )
    
    workflow_fig.update_layout(
        showlegend=False,
        height=200,
        margin=dict(l=20, r=20, t=20, b=100),
        xaxis=dict(showticklabels=False, zeroline=False, visible=False),
        yaxis=dict(showticklabels=False, zeroline=False, visible=False),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(workflow_fig, use_container_width=True)
    
    # Display agent interactions
    st.markdown("### Agent Interactions and Data Flow")
    
    # Create columns to display each agent's role in the ecosystem
    cols = st.columns(4)
    
    with cols[0]:
        st.markdown(explain_agent_role("proposer"), unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(explain_agent_role("simulator"), unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown(explain_agent_role("reviewer"), unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(explain_agent_role("consensus"), unsafe_allow_html=True)
    
    # Display key system features
    st.markdown("### Key System Features")
    
    features_cols = st.columns(3)
    
    with features_cols[0]:
        st.markdown("""
        <div class="agent-bg" style="padding: 15px; border-radius: 5px;">
            <h4>📊 Continuous Learning</h4>
            <p>All agents improve over time by learning from historical proposals, community feedback, and governance outcomes.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features_cols[1]:
        st.markdown("""
        <div class="agent-bg" style="padding: 15px; border-radius: 5px;">
            <h4>🔄 Transparent Process</h4>
            <p>Every step of the governance process is documented, with clear rationales for decisions and evaluations.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with features_cols[2]:
        st.markdown("""
        <div class="agent-bg" style="padding: 15px; border-radius: 5px;">
            <h4>⚡ Efficient Scaling</h4>
            <p>Autonomous agents enable parallel processing of multiple proposals, reducing bottlenecks in the governance process.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display system metrics
    st.markdown("### System Performance Metrics")
    
    metrics_cols = st.columns(4)
    
    # Define metrics
    system_metrics = [
        {"title": "Avg. Proposal Time", "value": "3.2 days"},
        {"title": "Review Accuracy", "value": "92%"},
        {"title": "Governance Throughput", "value": "+215%"},
        {"title": "Community Satisfaction", "value": "8.7/10"}
    ]
    
    # Display metrics in columns
    for i, metric in enumerate(system_metrics):
        with metrics_cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>{metric['title']}</h3>
                <p>{metric['value']}</p>
            </div>
            """, unsafe_allow_html=True)

# Auto navigation control
def auto_navigate():
    """Handle automatic navigation through workflow stages if enabled"""
    if st.session_state.get('auto_navigate', True):
        # Get current stage index
        current_index = WORKFLOW_STAGES.index(st.session_state.workflow_stage)
        
        # Check if we need to advance to the next stage
        if current_index < len(WORKFLOW_STAGES) - 1:
            # Schedule the next stage transition
            next_stage = WORKFLOW_STAGES[current_index + 1]
            st.session_state.next_stage_time = python_time.time() + 30  # Transition after 30 seconds
            
            # Display transition message
            if python_time.time() >= st.session_state.get('next_stage_time', 0):
                st.session_state.workflow_stage = next_stage
                st.experimental_rerun()

# Get or set the session state
if 'workflow_stage' not in st.session_state:
    st.session_state.workflow_stage = WORKFLOW_STAGES[0]

# Get or set auto-navigation
if 'auto_navigate' not in st.session_state:
    st.session_state.auto_navigate = True

# Set up the use_mcp state if not set
if 'use_mcp' not in st.session_state:
    st.session_state.use_mcp = False

# Get the MCP state
use_mcp = st.session_state.get('use_mcp', False)

# Check for auto-navigation
workflow_stage = st.session_state.workflow_stage
auto_navigate()

# Display the selected workflow stage
if workflow_stage == "1️⃣ Issue Identification":
    show_issue_identification()
elif workflow_stage == "2️⃣ EIP Creation":
    show_eip_creation()
elif workflow_stage == "3️⃣ Implementation & Testing":
    show_implementation_testing()
elif workflow_stage == "4️⃣ Review & Evaluation":
    show_review_evaluation()
elif workflow_stage == "5️⃣ Consensus Building":
    show_consensus_building()
elif workflow_stage == "6️⃣ Complete System Flow":
    show_complete_flow()

# Footer
st.markdown("---")
st.markdown("""
**Kephra Demo v0.2.0** | [GitHub Repository](https://github.com/summertinker/kephra) | [Documentation](https://kephra.readthedocs.io)
""")