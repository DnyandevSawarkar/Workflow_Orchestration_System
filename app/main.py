# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    try:
        # Try to set UTF-8 encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

# Set Groq API key
os.environ['GROQ_API_KEY_PROD4'] = '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'

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import asyncio
from temporalio.client import Client
from services.updated_services import ServiceRegistry
from services.groq_service import GroqLLMService

app = Flask(__name__)
CORS(app)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Temporal Workflow Orchestration System</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 10px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            box-sizing: border-box;
        }
        
        * {
            box-sizing: border-box;
        }
        
        .container { 
            max-width: 1200px; 
            width: 100%;
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { 
            color: #2c3e50; 
            text-align: center; 
            margin-bottom: 30px; 
            font-size: clamp(1.8rem, 4vw, 2.5rem);
            background: linear-gradient(135deg, #2c3e50, #34495e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        .service-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 15px; 
            margin-bottom: 30px; 
        }
        .service-card { 
            background: linear-gradient(135deg, #ffffff, #f8f9fa); 
            padding: 15px; 
            border-radius: 12px; 
            border-left: 5px solid #3498db; 
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            min-height: 120px;
        }
        .service-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 8px 25px rgba(52,152,219,0.2); 
        }
        .service-card.used {
            background: linear-gradient(135deg, #e8f5e8, #d4edda);
            border-left: 5px solid #27ae60;
            box-shadow: 0 8px 25px rgba(39,174,96,0.25);
        }
        .service-card.used::after {
            content: "✓ Used";
            position: absolute;
            top: 10px;
            right: 15px;
            background: #27ae60;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
        }
        .service-title { 
            font-weight: bold; 
            color: #2c3e50; 
            margin-bottom: 8px; 
            font-size: clamp(1.1rem, 3vw, 1.3rem);
            line-height: 1.3;
        }
        .service-desc { 
            font-size: clamp(0.95rem, 2.5vw, 1.05rem); 
            color: #7f8c8d; 
            line-height: 1.4;
        }
        
        .ai-banner {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 10px;
            font-weight: bold;
            font-size: clamp(1.1rem, 3vw, 1.3rem);
            line-height: 1.3;
        }
        .input-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        .input-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: clamp(1.1rem, 3vw, 1.3rem);
        }
        textarea { 
            width: 100%; 
            min-height: 100px;
            max-height: 200px;
            padding: 15px; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-family: inherit;
            font-size: clamp(16px, 3vw, 18px);
            resize: none;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        textarea:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52,152,219,0.1);
        }
        .button-container {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
            margin-top: 15px;
        }
        button { 
            background: linear-gradient(135deg, #3498db, #2980b9); 
            color: white; 
            padding: 12px 20px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: clamp(16px, 3vw, 18px);
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52,152,219,0.3);
            min-width: 140px;
            flex: 1;
            max-width: 300px;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52,152,219,0.4);
            background: linear-gradient(135deg, #2980b9, #1f5582);
        }
        button:active {
            transform: translateY(0);
        }
        button.secondary {
            background: linear-gradient(135deg, #95a5a6, #7f8c8d);
            box-shadow: 0 4px 15px rgba(149,165,166,0.3);
        }
        button.secondary:hover {
            box-shadow: 0 6px 20px rgba(149,165,166,0.4);
            background: linear-gradient(135deg, #7f8c8d, #6c7b7d);
        }
        
        /* Notification Styles */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
            max-width: 350px;
        }
        .notification.show {
            transform: translateX(0);
        }
        .notification.success {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
        }
        .notification.error {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        .notification.info {
            background: linear-gradient(135deg, #3498db, #2980b9);
        }
        .notification.warning {
            background: linear-gradient(135deg, #f39c12, #e67e22);
        }
        
        /* Progress Steps */
        .progress-container {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
            display: none;
        }
        .progress-steps {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .step {
            flex: 1;
            text-align: center;
            position: relative;
            min-width: 80px;
        }
        .step:not(:last-child):after {
            content: '';
            position: absolute;
            top: 15px;
            right: -50%;
            width: 100%;
            height: 2px;
            background: #ddd;
            z-index: 1;
        }
        .step.active:not(:last-child):after {
            background: #3498db;
        }
        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #bdc3c7;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 8px;
            font-weight: bold;
            position: relative;
            z-index: 2;
            transition: all 0.3s ease;
        }
        .step.active .step-circle {
            background: #3498db;
        }
        .step.completed .step-circle {
            background: #27ae60;
        }
        .step-label {
            font-size: clamp(12px, 2.5vw, 14px);
            color: #7f8c8d;
            word-wrap: break-word;
            hyphens: auto;
        }
        .step.active .step-label {
            color: #3498db;
            font-weight: bold;
        }
        
        /* Results */
        .results-container {
            margin-top: 30px;
        }
        .result-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .result-header {
            padding: 15px 20px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .result-header.success {
            background: #d4f6d4;
            color: #2d5a2d;
        }
        .result-header.error {
            background: #f8d7da;
            color: #721c24;
        }
        .result-body {
            padding: 20px;
        }
        .retry-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }
        .retry-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .retry-btn {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: clamp(14px, 2.5vw, 16px);
            font-weight: 500;
            transition: all 0.3s ease;
            flex: 1;
            min-width: 120px;
            text-align: center;
        }
        .retry-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(243,156,18,0.4);
        }
        .retry-btn.email {
            background: linear-gradient(135deg, #3498db, #2980b9);
        }
        .retry-btn.email:hover {
            box-shadow: 0 4px 12px rgba(52,152,219,0.4);
        }
        .retry-btn.sms {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
        }
        .retry-btn.sms:hover {
            box-shadow: 0 4px 12px rgba(39,174,96,0.4);
        }
        .retry-btn.call {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        .retry-btn.call:hover {
            box-shadow: 0 4px 12px rgba(231,76,60,0.4);
        }
        .hidden {
            display: none;
        }
        
        /* Summary Markdown Styles */
        .summary-card .result-body h1 {
            color: #2c3e50;
            font-size: 1.5rem;
            margin-bottom: 15px;
            border-bottom: 2px solid #28a745;
            padding-bottom: 8px;
        }
        
        .summary-card .result-body h2 {
            color: #34495e;
            font-size: 1.2rem;
            margin-top: 20px;
            margin-bottom: 10px;
            border-left: 4px solid #28a745;
            padding-left: 12px;
        }
        
        .summary-card .result-body ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .summary-card .result-body li {
            margin: 5px 0;
            line-height: 1.4;
        }
        
        .summary-card .result-body strong {
            color: #2c3e50;
        }
        
        .summary-card .result-body em {
            color: #27ae60;
            font-style: normal;
            font-weight: 500;
        }
        
        .summary-card .result-body code {
            background: #f8f9fa;
            color: #e74c3c;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .summary-card .result-body blockquote {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 12px 15px;
            border-radius: 4px;
            font-style: italic;
        }
        
        .summary-card .result-body blockquote strong {
            color: #3498db;
        }
        
        @keyframes highlight {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        
        .result-card {
            animation: slideIn 0.5s ease-out;
        }
        
        .step.active .step-circle {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        button:disabled {
            cursor: not-allowed;
            opacity: 0.7 !important;
            transform: none !important;
        }
        
        /* Loading state for progress steps */
        .step.processing .step-circle {
            background: linear-gradient(45deg, #3498db, #2980b9, #3498db);
            background-size: 200% 200%;
            animation: shimmer 2s ease-in-out infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Media Queries for Responsive Design */
        
        /* Tablet styles */
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }
            
            .container {
                padding: 15px;
                border-radius: 10px;
            }
            
            .service-grid {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 12px;
            }
            
            .service-card {
                padding: 12px;
                min-height: 100px;
            }
            
            .progress-steps {
                justify-content: center;
                gap: 8px;
            }
            
            .step {
                min-width: 70px;
            }
            
            .button-container {
                flex-direction: column;
                align-items: stretch;
            }
            
            button {
                max-width: none;
                width: 100%;
            }
            
            .ai-banner {
                margin: 15px 0;
                padding: 12px;
                font-size: clamp(1.0rem, 3vw, 1.2rem);
            }
        }
        
        /* Mobile styles */
        @media (max-width: 480px) {
            body {
                padding: 2px;
            }
            
            .container {
                padding: 10px;
                border-radius: 8px;
                margin: 2px;
            }
            
            .service-grid {
                grid-template-columns: 1fr;
                gap: 10px;
            }
            
            .service-card {
                padding: 10px;
                min-height: 80px;
            }
            
            .service-card.used::after {
                font-size: 10px;
                padding: 3px 8px;
                top: 8px;
                right: 12px;
            }
            
            .progress-steps {
                flex-direction: column;
                gap: 15px;
            }
            
            .step {
                min-width: 100%;
                margin-bottom: 10px;
            }
            
            .step:not(:last-child):after {
                display: none;
            }
            
            .retry-buttons {
                flex-direction: column;
                gap: 5px;
            }
            
            .retry-btn {
                min-width: 100%;
                width: 100%;
            }
            
            .input-section {
                padding: 15px;
            }
            
            textarea {
                min-height: 90px;
                padding: 15px;
            }
            
            .notification {
                max-width: calc(100vw - 20px);
                right: 10px;
                top: 10px;
            }
            
            .ai-banner {
                margin: 10px 0;
                padding: 10px;
                font-size: clamp(0.9rem, 3vw, 1.1rem);
                border-radius: 8px;
            }
        }
        
        /* Large screen optimization */
        @media (min-width: 1200px) {
            .container {
                padding: 40px;
            }
            
            .service-grid {
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
            }
            
            .input-section {
                padding: 30px;
            }
        }
        
        /* Markdown styling for summary content */
        .result-body h1,
        .result-body h2,
        .result-body h3,
        .result-body h4,
        .result-body h5,
        .result-body h6 {
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .result-body h1 { font-size: 1.8rem; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .result-body h2 { font-size: 1.5rem; border-bottom: 1px solid #e9ecef; padding-bottom: 8px; }
        .result-body h3 { font-size: 1.3rem; }
        .result-body h4 { font-size: 1.1rem; color: #34495e; }
        
        .result-body p {
            margin-bottom: 12px;
            line-height: 1.6;
            color: #2c3e50;
        }
        
        .result-body strong,
        .result-body b {
            color: #2c3e50;
            font-weight: 600;
        }
        
        .result-body ul,
        .result-body ol {
            margin-bottom: 15px;
            padding-left: 25px;
        }
        
        .result-body li {
            margin-bottom: 6px;
            line-height: 1.5;
        }
        
        .result-body blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 15px 0;
            background: #f8f9fa;
            font-style: italic;
            color: #5a6c7d;
        }
        
        .result-body code {
            background: #f1f2f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            color: #e74c3c;
        }
        
        .result-body pre {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
        }
        
        .result-body pre code {
            background: none;
            padding: 0;
            color: #2c3e50;
        }
        
        .result-body table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        
        .result-body th,
        .result-body td {
            border: 1px solid #e9ecef;
            padding: 10px;
            text-align: left;
        }
        
        .result-body th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .result-body hr {
            border: none;
            border-top: 2px solid #e9ecef;
            margin: 20px 0;
        }
        
        /* Animation styles for realistic workflow progression */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        
        @keyframes shimmer {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .result-card {
            animation: slideIn 0.5s ease-out;
        }
        
        .step.active .step-circle {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        .step.processing .step-circle {
            background: linear-gradient(45deg, #3498db, #2980b9, #3498db);
            background-size: 200% 200%;
            animation: shimmer 2s ease-in-out infinite;
        }
        
        button:disabled {
            cursor: not-allowed;
            opacity: 0.7 !important;
            transform: none !important;
        }
        
        /* Loading indicator for active steps */
        .step.active .step-label {
            position: relative;
        }
        
        .step.active .step-label::after {
            content: '...';
            animation: dots 1.5s steps(3, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: ''; }
            40% { content: '.'; }
            60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Temporal Workflow Orchestration System</h1>
        
        <div class="ai-banner">
            🤖 AI-Powered Services & Advanced Workflow Orchestration
        </div>
        
        <div class="service-grid">
            <div class="service-card" id="service-order">
                <div class="service-title">Order Creation</div>
                <div class="service-desc">Simulates receiving and processing orders</div>
            </div>
            <div class="service-card" id="service-payment">
                <div class="service-title">Payment Processing</div>
                <div class="service-desc">Secure payment processing with retry logic</div>
            </div>
            <div class="service-card" id="service-currency">
                <div class="service-title">Currency Conversion</div>
                <div class="service-desc">Real-time currency conversion with fallbacks</div>
            </div>
            <div class="service-card" id="service-email">
                <div class="service-title">Email Notification</div>
                <div class="service-desc">Automated confirmation emails</div>
            </div>
            <div class="service-card" id="service-shipping">
                <div class="service-title">Shipping Confirmation</div>
                <div class="service-desc">Shipping arrangements and tracking</div>
            </div>
            <div class="service-card" id="service-call">
                <div class="service-title">Call Center</div>
                <div class="service-desc">Customer support escalation</div>
            </div>
            <div class="service-card" id="service-sms">
                <div class="service-title">SMS Notifications</div>
                <div class="service-desc">Real-time SMS alerts and updates</div>
            </div>
            <div class="service-card" id="service-booking">
                <div class="service-title">Booking Management</div>
                <div class="service-desc">Advanced reservation and booking handling</div>
            </div>
        </div>
        
        <div class="input-section">
            <h3>Natural Language Input</h3>
            <textarea id="userInput" placeholder="Try examples like:
• 'Order 2 wireless headphones for personal use'
• 'Book a flight from NYC to Paris for business trip'
• 'Purchase 10 software licenses for our team'
• 'Reserve a conference room and catering for 50 people'"></textarea>
            
            <div class="button-container">
                <button onclick="executeWorkflow()">Process Request</button>
            </div>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-steps" id="progressSteps">
                <!-- Dynamic steps will be generated here -->
            </div>
        </div>
        
        <div class="results-container" id="resultsContainer"></div>
    </div>

    <script>
        let currentNotification = null;
        
        function showNotification(message, type = 'info', duration = 4000) {
            // Remove existing notification
            if (currentNotification) {
                currentNotification.remove();
            }
            
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            currentNotification = notification;
            
            // Show notification
            setTimeout(() => notification.classList.add('show'), 100);
            
            // Hide notification
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                    if (currentNotification === notification) {
                        currentNotification = null;
                    }
                }, 300);
            }, duration);
        }
        
        function showProgress() {
            document.getElementById('progressContainer').style.display = 'block';
            // Reset all steps
            document.querySelectorAll('.step').forEach(step => {
                step.className = 'step';
            });
        }
        
        function hideProgress() {
            document.getElementById('progressContainer').style.display = 'none';
        }
        
        function generateProgressSteps(workflowSteps) {
            const container = document.getElementById('progressSteps');
            container.innerHTML = '';
            
            workflowSteps.forEach((stepName, index) => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'step';
                stepDiv.setAttribute('data-step', `step-${index}`);
                
                stepDiv.innerHTML = `
                    <div class="step-circle">${index + 1}</div>
                    <div class="step-label">${stepName}</div>
                `;
                
                container.appendChild(stepDiv);
            });
        }
        
        function updateProgressStep(stepIndex, status = 'active') {
            const step = document.querySelector(`[data-step="step-${stepIndex}"]`);
            if (step) {
                step.className = `step ${status}`;
            }
        }
        
        function displayWorkflowConfig(config) {
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '';
            
            const card = document.createElement('div');
            card.className = 'result-card';
            
            const header = document.createElement('div');
            header.className = 'result-header success';
            header.innerHTML = '✅ Request Analyzed Successfully';
            
            const body = document.createElement('div');
            body.className = 'result-body';
            
            const details = `
                <h4>Service Details:</h4>
                <p><strong>Service Type:</strong> ${config.workflow_type || 'General Service'}</p>
                <p><strong>Category:</strong> ${config.domain || 'General'}</p>
                <p><strong>Service Level:</strong> ${config.service_level || 'Standard'}</p>
                <p><strong>Payment Method:</strong> ${config.payment_method || 'Credit Card'}</p>
                
                <h4>Items/Services:</h4>
                <ul>
                    ${config.items ? config.items.map(item => 
                        `<li>${item.quantity || 1}x ${item.name || 'Service'} - $${item.price || 0}</li>`
                    ).join('') : '<li>No items specified</li>'}
                </ul>
                
                <h4>Customer Information:</h4>
                <p><strong>Customer ID:</strong> ${config.customer_id || 'Generated'}</p>
                <p><strong>Email:</strong> ${config.customer_email || 'Not specified'}</p>
                <p><strong>Delivery Timeline:</strong> ${config.delivery_timeline || 'Standard'}</p>
            `;
            
            body.innerHTML = details;
            card.appendChild(header);
            card.appendChild(body);
            container.appendChild(card);
        }
        
        function highlightUsedServices(results) {
            // Reset all service cards first
            document.querySelectorAll('.service-card').forEach(card => {
                card.classList.remove('used');
            });
            
            // Map service keys to their corresponding DOM elements
            const serviceMapping = {
                'order': 'service-order',
                'payment': 'service-payment', 
                'currency': 'service-currency',
                'email': 'service-email',
                'shipping': 'service-shipping',
                'call': 'service-call',
                'sms': 'service-sms',
                'booking': 'service-booking'
            };
            
            // Highlight services that were used
            Object.keys(results).forEach(serviceKey => {
                const elementId = serviceMapping[serviceKey];
                if (elementId) {
                    const serviceElement = document.getElementById(elementId);
                    if (serviceElement) {
                        serviceElement.classList.add('used');
                        
                        // Add a subtle animation
                        serviceElement.style.animation = 'none';
                        setTimeout(() => {
                            serviceElement.style.animation = 'highlight 0.8s ease-in-out';
                        }, 100);
                    }
                }
            });
        }
        
        function displayExecutionResults(results, workflowSteps = null) {
            const container = document.getElementById('resultsContainer');
            container.innerHTML = '';
            
            // Check if summary exists and display it first
            if (results.summary && results.summary.success && results.summary.data) {
                const summaryCard = document.createElement('div');
                summaryCard.className = 'result-card summary-card';
                summaryCard.style.cssText = `
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                    border: 2px solid #28a745;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 20px rgba(40,167,69,0.15);
                `;
                
                const summaryHeader = document.createElement('div');
                summaryHeader.className = 'result-header success';
                summaryHeader.style.cssText = `
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    font-size: 1.2rem;
                    font-weight: bold;
                `;
                summaryHeader.innerHTML = '📋 Order Complete - Summary';
                
                const summaryBody = document.createElement('div');
                summaryBody.className = 'result-body';
                summaryBody.style.cssText = `
                    font-size: 1rem;
                    line-height: 1.6;
                `;
                
                // Convert markdown to HTML
                if (typeof marked !== 'undefined') {
                    summaryBody.innerHTML = marked.parse(results.summary.data.summary_text);
                } else {
                    // Fallback if marked.js doesn't load
                    summaryBody.style.whiteSpace = 'pre-line';
                    summaryBody.innerHTML = results.summary.data.summary_text;
                }
                
                summaryCard.appendChild(summaryHeader);
                summaryCard.appendChild(summaryBody);
                container.appendChild(summaryCard);
            }
            
            // Dynamic service mapping based on workflow steps if available
            const getServiceInfo = (service, index) => {
                if (workflowSteps && workflowSteps[index]) {
                    return { name: workflowSteps[index], icon: '✓' };
                }
                
                // Fallback to user-friendly names (no technical terms)
                const serviceMap = {
                    'analysis': { name: 'Request Analysis', icon: '📋' },
                    'order': { name: 'Service Setup', icon: '🔧' },
                    'payment': { name: 'Payment Processing', icon: '💳' },
                    'shipping': { name: 'Delivery Arrangement', icon: '📦' },
                    'email': { name: 'Email Notification', icon: '📧' },
                    'sms': { name: 'SMS Notification', icon: '📱' },
                    'summary': { name: 'Order Summary', icon: '�' }
                };
                
                return serviceMap[service] || { name: 'Service Processing', icon: '⚙️' };
            };
            
            // Display service details (exclude summary as it's shown above)
            Object.entries(results).forEach(([service, result], index) => {
                if (service === 'summary') return; // Skip summary as it's displayed above
                
                const serviceInfo = getServiceInfo(service, index);
                
                const card = document.createElement('div');
                card.className = 'result-card';
                
                const header = document.createElement('div');
                header.className = `result-header ${result.success ? 'success' : 'error'}`;
                header.innerHTML = `${serviceInfo.icon} ${serviceInfo.name} ${result.success ? '✅' : '❌'}`;
                
                const body = document.createElement('div');
                body.className = 'result-body';
                
                if (result.success && result.data) {
                    let details = '';
                    if (service === 'analysis' && result.data.status) {
                        details = `
                            <strong>Status:</strong> ${result.data.status}<br>
                            <strong>Type:</strong> ${result.data.workflow_type}<br>
                            <strong>Items:</strong> ${result.data.total_items}<br>
                            <strong>Estimated Total:</strong> ${result.data.currency} ${result.data.estimated_total}
                        `;
                    } else if (service === 'order' && result.data.order_id) {
                        details = `<strong>Reference ID:</strong> ${result.data.order_id}`;
                    } else if (service === 'payment' && result.data.payment_id) {
                        details = `
                            <strong>Payment ID:</strong> ${result.data.payment_id}<br>
                            <strong>Amount:</strong> ${result.data.currency_display || '$' + result.data.amount + ' USD'}<br>
                            <strong>Status:</strong> ${result.data.status}
                        `;
                    } else if (service === 'shipping' && result.data.tracking_number) {
                        details = `<strong>Tracking Number:</strong> ${result.data.tracking_number}`;
                    } else if (service === 'email' && result.data.email_id) {
                        details = `<strong>Email ID:</strong> ${result.data.email_id}`;
                    } else if (service === 'sms' && result.data.sms_id) {
                        details = `<strong>SMS ID:</strong> ${result.data.sms_id}`;
                    } else if (result.data.message) {
                        details = result.data.message;
                    }
                    body.innerHTML = `<p>✅ Completed Successfully</p>${details ? `<p>${details}</p>` : ''}`;
                } else {
                    const errorMsg = `<p>❌ Service temporarily unavailable</p>`;
                    
                    // Add retry options for failed services (excluding analysis)
                    if (service !== 'analysis') {
                        const retrySection = `
                            <div class="retry-section">
                                <p><strong>Recovery Options:</strong></p>
                                <div class="retry-buttons">
                                    <button class="retry-btn email" onclick="retryWithNotification('${service}', 'email')">
                                        📧 Retry + Email Alert
                                    </button>
                                    <button class="retry-btn sms" onclick="retryWithNotification('${service}', 'sms')">
                                        📱 Retry + SMS Alert
                                    </button>
                                    <button class="retry-btn call" onclick="retryWithNotification('${service}', 'call')">
                                        📞 Retry + Support Call
                                    </button>
                                </div>
                            </div>
                        `;
                        body.innerHTML = errorMsg + retrySection;
                    } else {
                        body.innerHTML = errorMsg;
                    }
                }
                
                card.appendChild(header);
                card.appendChild(body);
                container.appendChild(card);
            });
            
            // Highlight the services that were used
            highlightUsedServices(results);
        }
        
        function displayServiceResult(serviceKey, result, serviceName, stepIndex) {
            const container = document.getElementById('resultsContainer');
            
            // Get service info
            const serviceMap = {
                'analysis': { name: 'Request Analysis', icon: '📋' },
                'order': { name: 'Service Setup', icon: '🔧' },
                'payment': { name: 'Payment Processing', icon: '💳' },
                'shipping': { name: 'Delivery Arrangement', icon: '📦' },
                'email': { name: 'Email Notification', icon: '📧' },
                'sms': { name: 'SMS Notification', icon: '📱' },
                'booking': { name: 'Booking Management', icon: '📅' }
            };
            
            const serviceInfo = serviceMap[serviceKey] || { name: serviceName, icon: '⚙️' };
            
            const card = document.createElement('div');
            card.className = 'result-card';
            card.style.animation = 'slideIn 0.5s ease-out';
            card.setAttribute('data-service', serviceKey);
            
            const header = document.createElement('div');
            header.className = `result-header ${result.success ? 'success' : 'error'}`;
            header.innerHTML = `${serviceInfo.icon} ${serviceInfo.name} ${result.success ? '✅' : '❌'}`;
            
            const body = document.createElement('div');
            body.className = 'result-body';
            
            if (result.success && result.data) {
                let details = '';
                if (serviceKey === 'analysis' && result.data.status) {
                    details = `
                        <strong>Status:</strong> ${result.data.status}<br>
                        <strong>Type:</strong> ${result.data.workflow_type}<br>
                        <strong>Items:</strong> ${result.data.total_items}<br>
                        <strong>Estimated Total:</strong> ${result.data.currency} ${result.data.estimated_total}
                    `;
                } else if (serviceKey === 'order' && result.data.order_id) {
                    details = `<strong>Reference ID:</strong> ${result.data.order_id}`;
                } else if (serviceKey === 'payment' && result.data.payment_id) {
                    details = `
                        <strong>Payment ID:</strong> ${result.data.payment_id}<br>
                        <strong>Amount:</strong> ${result.data.currency_display || '$' + result.data.amount + ' USD'}<br>
                        <strong>Status:</strong> ${result.data.status}
                    `;
                } else if (serviceKey === 'shipping' && result.data.tracking_number) {
                    details = `<strong>Tracking Number:</strong> ${result.data.tracking_number}`;
                } else if (serviceKey === 'email' && result.data.email_id) {
                    details = `<strong>Email ID:</strong> ${result.data.email_id}`;
                } else if (serviceKey === 'sms' && result.data.sms_id) {
                    details = `<strong>SMS ID:</strong> ${result.data.sms_id}`;
                } else if (result.data.message) {
                    details = result.data.message;
                }
                body.innerHTML = `<p>✅ Completed Successfully</p>${details ? `<p>${details}</p>` : ''}`;
            } else {
                const errorMsg = `<p>❌ Service temporarily unavailable</p>`;
                
                // Add retry options for failed services (excluding analysis)
                if (serviceKey !== 'analysis') {
                    const retrySection = `
                        <div class="retry-section">
                            <p><strong>Recovery Options:</strong></p>
                            <div class="retry-buttons">
                                <button class="retry-btn email" onclick="retryWithNotification('${serviceKey}', 'email')">
                                    📧 Retry + Email Alert
                                </button>
                                <button class="retry-btn sms" onclick="retryWithNotification('${serviceKey}', 'sms')">
                                    📱 Retry + SMS Alert
                                </button>
                                <button class="retry-btn call" onclick="retryWithNotification('${serviceKey}', 'call')">
                                    📞 Retry + Support Call
                                </button>
                            </div>
                        </div>
                    `;
                    body.innerHTML = errorMsg + retrySection;
                } else {
                    body.innerHTML = errorMsg;
                }
            }
            
            card.appendChild(header);
            card.appendChild(body);
            container.appendChild(card);
            
            // Scroll to the new card
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        function displaySummaryResult(summaryResult) {
            if (!summaryResult.success || !summaryResult.data) return;
            
            const container = document.getElementById('resultsContainer');
            
            // Create summary card at the top
            const summaryCard = document.createElement('div');
            summaryCard.className = 'result-card summary-card';
            summaryCard.style.cssText = `
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border: 2px solid #28a745;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(40,167,69,0.15);
                animation: slideIn 0.8s ease-out;
            `;
            
            const summaryHeader = document.createElement('div');
            summaryHeader.className = 'result-header success';
            summaryHeader.style.cssText = `
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                font-size: 1.2rem;
                font-weight: bold;
            `;
            summaryHeader.innerHTML = '📋 Order Complete - Summary';
            
            const summaryBody = document.createElement('div');
            summaryBody.className = 'result-body';
            summaryBody.style.cssText = `
                font-size: 1rem;
                line-height: 1.6;
            `;
            
            // Convert markdown to HTML
            if (typeof marked !== 'undefined') {
                summaryBody.innerHTML = marked.parse(summaryResult.data.summary_text);
            } else {
                // Fallback if marked.js doesn't load
                summaryBody.style.whiteSpace = 'pre-line';
                summaryBody.innerHTML = summaryResult.data.summary_text;
            }
            
            summaryCard.appendChild(summaryHeader);
            summaryCard.appendChild(summaryBody);
            
            // Insert at the top
            container.insertBefore(summaryCard, container.firstChild);
            
            // Scroll to top to show summary
            summaryCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
                async function executeWorkflow() {
            const input = document.getElementById('userInput').value;
            if (!input.trim()) {
                showNotification('Please enter some text to execute', 'warning');
                return;
            }
            
            // Disable button during execution
            const button = document.querySelector('button');
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Processing...';
            button.style.opacity = '0.7';
            
            // Clear previous results
            document.getElementById('resultsContainer').innerHTML = '';
            
            showNotification('Starting workflow execution...', 'info');
            
            try {
                // Step 1: Initial request to get configuration
                showNotification('📋 Analyzing your request...', 'info');
                
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: input })
                });
                const result = await response.json();
                
                if (result.success) {
                    // Get workflow steps and results
                    const workflowSteps = result.workflow_steps || ['Reviewing Request', 'Setting Up Service', 'Processing Payment', 'Arranging Delivery', 'Sending Confirmation'];
                    const results = result.results;
                    
                    generateProgressSteps(workflowSteps);
                    showProgress();
                    
                    // Step 2: Show each workflow step with realistic timing
                    for (let i = 0; i < workflowSteps.length; i++) {
                        updateProgressStep(i, 'active');
                        
                        // Show step-specific notification
                        const stepName = workflowSteps[i];
                        showNotification(`🔄 ${stepName} in progress...`, 'info');
                        
                        // Realistic delays for different steps
                        const stepDelays = {
                            0: 1500, // Review Request
                            1: 2200, // Service Setup  
                            2: 2800, // Payment Processing
                            3: 1800, // Delivery Arrangement
                            4: 1200  // Confirmation
                        };
                        
                        const delay = stepDelays[i] || 1500;
                        await new Promise(resolve => setTimeout(resolve, delay));
                        
                        // Complete the step
                        updateProgressStep(i, 'completed');
                        showNotification(`✅ ${stepName} completed!`, 'success');
                        
                        // Small pause between steps
                        await new Promise(resolve => setTimeout(resolve, 400));
                    }
                    
                    // Show final results
                    showNotification('🎉 Workflow completed successfully!', 'success');
                    displayExecutionResults(result.results, workflowSteps);
                    
                } else {
                    hideProgress();
                    showNotification(`Execution failed: ${result.error_message}`, 'error');
                }
            } catch (error) {
                hideProgress();
                showNotification(`❌ Error: ${error.message}`, 'error');
            } finally {
                // Re-enable button
                button.disabled = false;
                button.textContent = originalText;
                button.style.opacity = '1';
            }
        }
        
        async function retryWithNotification(serviceName, notificationType) {
            const input = document.getElementById('userInput').value;
            if (!input.trim()) {
                showNotification('Please enter some text to retry', 'warning');
                return;
            }
            
            showNotification(`Retrying ${serviceName} service with ${notificationType} notification...`, 'info');
            
            try {
                const response = await fetch('/api/retry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        input: input,
                        service: serviceName,
                        notification_type: notificationType
                    })
                });
                const result = await response.json();
                
                if (result.success) {
                    showNotification(`${serviceName} service retry successful! ${notificationType} notification sent.`, 'success');
                    // Update the result display with workflow steps
                    const workflowSteps = result.workflow_steps || ['Processing Request', 'Completing Setup', 'Finalizing', 'Sending Confirmation'];
                    displayExecutionResults(result.results, workflowSteps);
                } else {
                    showNotification(`Retry failed: ${result.error_message}`, 'error');
                }
            } catch (error) {
                showNotification(`❌ Retry error: ${error.message}`, 'error');
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/parse', methods=['POST'])
def parse_workflow():
    try:
        data = request.json
        if not data or 'input' not in data:
            return jsonify({'success': False, 'error_message': 'Missing input data'})
        
        user_input = data['input'].strip()
        if not user_input:
            return jsonify({'success': False, 'error_message': 'Empty input provided'})
        
        groq_service = GroqLLMService()
        result = groq_service.execute(user_input)
        
        return jsonify({
            'success': result.success,
            'data': result.data,
            'error_message': result.error_message
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return jsonify({
            'success': False, 
            'error_message': f'Server error: {str(e)}',
            'details': error_details
        })

@app.route('/api/execute', methods=['POST'])
def execute_workflow():
    try:
        data = request.json
        
        # This would typically trigger a Temporal workflow
        # For now, we'll simulate the execution
        registry = ServiceRegistry()
        groq_service = GroqLLMService()
        
        # Parse input
        parse_result = groq_service.execute(data['input'])
        if not parse_result.success:
            return jsonify({'success': False, 'error_message': parse_result.error_message})
        
        config = parse_result.data['workflow_config']
        
        # Initialize results dictionary
        results = {}
        
        # Step 1: Review Request (Always succeeds - it's just analysis)
        results['analysis'] = {
            'success': True, 
            'data': {
                'status': 'analyzed',
                'workflow_type': config.get('workflow_type', 'service_request'),
                'domain': config.get('domain', 'general'),
                'total_items': len(config.get('items', [])),
                'estimated_total': sum(item['price'] * item['quantity'] for item in config.get('items', [])),
                'currency': config.get('currency', 'USD'),
                'message': 'Request successfully analyzed and validated'
            }
        }
        
        # Step 2: Order/Service Creation
        order_service = registry.get_service('order_creation')
        order_result = order_service.execute(
            customer_id=config['customer_id'],
            items=config['items'],
            channel=config['channel']
        )
        results['order'] = {'success': order_result.success, 'data': order_result.data}
        
        if order_result.success:
            # Step 3: Payment processing (Can fail)
            payment_service = registry.get_service('payment_processing')
            payment_result = payment_service.execute(
                amount=sum(item['price'] * item['quantity'] for item in config['items']),
                customer_id=config['customer_id'],
                currency=config.get('currency', 'USD')
            )
            results['payment'] = {'success': payment_result.success, 'data': payment_result.data}
            
            # Step 4: Shipping/Delivery (Can fail)
            if payment_result.success:
                shipping_service = registry.get_service('shipping_confirmation')
                shipping_result = shipping_service.execute(order_id=order_result.data['order_id'])
                results['shipping'] = {'success': shipping_result.success, 'data': shipping_result.data}
            
            # Step 5: Notifications (Can fail)
            email_service = registry.get_service('email_notification')
            email_result = email_service.execute(
                recipient=config['customer_email'],
                subject=f"Order Confirmation - {order_result.data['order_id']}"
            )
            results['email'] = {'success': email_result.success, 'data': email_result.data}
            
            # SMS notification (Can fail)
            sms_service = registry.get_service('sms_notification')
            sms_result = sms_service.execute(
                phone_number=config.get('customer_phone', '+1-555-0123'),
                message=f"Order {order_result.data['order_id']} confirmed. Total: ${results['payment']['data'].get('amount', 0)}"
            )
            results['sms'] = {'success': sms_result.success, 'data': sms_result.data}
        
        # Final Step: Generate LLM Summary (Always runs, very low failure rate)
        summary_service = registry.get_service('order_summary')
        summary_result = summary_service.execute(config=config, results=results)
        results['summary'] = {'success': summary_result.success, 'data': summary_result.data}
        
        # Get workflow steps from LLM response
        workflow_steps = config.get('workflow_steps', [
            'Request Analysis', 'Service Setup', 'Payment Processing', 'Service Arrangement', 'Confirmation Delivery'
        ])
        
        return jsonify({
            'success': True, 
            'results': results,
            'workflow_steps': workflow_steps
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)})

@app.route('/api/retry', methods=['POST'])
def retry_service():
    """Retry a failed service with notification"""
    try:
        data = request.json
        service_name = data['service']
        notification_type = data['notification_type']
        user_input = data['input']
        
        registry = ServiceRegistry()
        groq_service = GroqLLMService()
        
        # Parse input again to get config
        parse_result = groq_service.execute(user_input)
        if not parse_result.success:
            return jsonify({'success': False, 'error_message': 'Failed to process input for retry'})
        
        config = parse_result.data['workflow_config']
        workflow_steps = config.get('workflow_steps', [
            'Request Analysis', 'Service Setup', 'Payment Processing', 'Service Arrangement', 'Confirmation Delivery'
        ])
        results = {}
        
        # Retry the specific service
        if service_name == 'order':
            service = registry.get_service('order_creation')
            result = service.execute(
                customer_id=config['customer_id'],
                items=config['items'],
                channel=config['channel']
            )
            results['order'] = {'success': result.success, 'data': result.data}
            
        elif service_name == 'payment':
            service = registry.get_service('payment_processing')
            result = service.execute(
                amount=sum(item['price'] * item['quantity'] for item in config['items']),
                customer_id=config['customer_id']
            )
            results['payment'] = {'success': result.success, 'data': result.data}
            
        elif service_name == 'shipping':
            # For shipping, we need an order_id - use a dummy one for retry
            service = registry.get_service('shipping_confirmation')
            result = service.execute(order_id=config.get('order_id', 'RETRY-ORDER-001'))
            results['shipping'] = {'success': result.success, 'data': result.data}
            
        elif service_name == 'email':
            service = registry.get_service('email_notification')
            result = service.execute(
                recipient=config['customer_email'],
                subject="Service Retry Notification"
            )
            results['email'] = {'success': result.success, 'data': result.data}
        
        # Send notification based on type
        if notification_type == 'email':
            email_service = registry.get_service('email_notification')
            email_service.execute(
                recipient=config['customer_email'],
                subject=f"Service Retry Alert - {service_name.title()} Service"
            )
        elif notification_type == 'sms':
            sms_service = registry.get_service('sms_notification')
            sms_service.execute(
                phone_number=config.get('customer_phone', '+1234567890'),
                message=f"Service retry initiated for {service_name.title()} service"
            )
        elif notification_type == 'call':
            call_service = registry.get_service('call_center_trigger')
            call_service.execute(
                customer_id=config['customer_id'],
                phone_number=config.get('customer_phone', '+1234567890')
            )
        
        return jsonify({
            'success': True, 
            'results': results,
            'workflow_steps': workflow_steps
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)})

if __name__ == '__main__':
    print("Starting Flask Web UI on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
