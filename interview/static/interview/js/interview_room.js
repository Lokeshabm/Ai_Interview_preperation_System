/**
 * AI Interview Room Engine
 * Handles Webcam, Microphone, Web Audio Waveforms, SpeechSynthesis, SpeechRecognition,
 * Monaco Editor, and Automatic Question Type Switching.
 */

let currentQuestionIndex = 0;
let mediaStream = null;
let audioContext = null;
let analyserNode = null;
let animationFrameId = null;
let speechRecognition = null;
let isRecognizing = false;
let monacoEditorInstance = null;
let timerSecondsRemaining = typeof DURATION_SECONDS !== 'undefined' ? DURATION_SECONDS : 1800;
let timerInterval = null;

// DOM Elements
const webcamVideo = document.getElementById('webcamPreview');
const waveformCanvas = document.getElementById('waveformCanvas');
const sessionTimerDisplay = document.getElementById('sessionTimerDisplay');
const questionTracker = document.getElementById('questionTracker');
const interviewProgressBar = document.getElementById('interviewProgressBar');
const questionStatementText = document.getElementById('questionStatementText');
const questionCategoryBadge = document.getElementById('questionCategoryBadge');
const questionDifficultyBadge = document.getElementById('questionDifficultyBadge');
const aiInterviewerStatus = document.getElementById('aiInterviewerStatus');
const aiHintBox = document.getElementById('aiHintBox');

// Media buttons
const toggleCameraBtn = document.getElementById('toggleCameraBtn');
const toggleMicBtn = document.getElementById('toggleMicBtn');
const cameraIcon = document.getElementById('cameraIcon');
const micIcon = document.getElementById('micIcon');
const repeatQuestionBtn = document.getElementById('repeatQuestionBtn');
const stopSpeechBtn = document.getElementById('stopSpeechBtn');
const finishInterviewBtn = document.getElementById('finishInterviewBtn');

// Workspace Containers
const voiceWorkspaceCard = document.getElementById('voiceWorkspaceCard');
const codingWorkspaceCard = document.getElementById('codingWorkspaceCard');
const candidateAnswerInput = document.getElementById('candidateAnswerInput');
const toggleSpeechBtn = document.getElementById('toggleSpeechRecognitionBtn');
const speechBtnText = document.getElementById('speechBtnText');
const speechRecognitionStatus = document.getElementById('speechRecognitionStatus');
const submitOralAnswerBtn = document.getElementById('submitOralAnswerBtn');
const clearAnswerBtn = document.getElementById('clearAnswerBtn');
const instantFeedbackBox = document.getElementById('instantFeedbackBox');
const feedbackScore = document.getElementById('feedbackScore');
const feedbackStrengths = document.getElementById('feedbackStrengths');
const feedbackFollowUp = document.getElementById('feedbackFollowUp');

// Coding Elements
const codeLanguageSelect = document.getElementById('codeLanguageSelect');
const runCodeBtn = document.getElementById('runCodeBtn');
const submitCodeBtn = document.getElementById('submitCodeBtn');
const consoleOutputArea = document.getElementById('consoleOutputArea');
const executionMetaText = document.getElementById('executionMetaText');

// Language starter templates
const DEFAULT_CODE_SNIPPETS = {
    python: 'def solution():\n    # Write your solution here\n    pass\n\nif __name__ == "__main__":\n    solution()\n',
    javascript: 'function solution() {\n    // Write your code here\n}\nsolution();\n',
    java: 'import java.util.*;\n\npublic class Solution {\n    public static void main(String[] args) {\n        // Your code here\n    }\n}\n',
    cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n    // Your code here\n    return 0;\n}\n',
    c: '#include <stdio.h>\n\nint main() {\n    // Your code here\n    return 0;\n}\n'
};

document.addEventListener('DOMContentLoaded', () => {
    initMediaStreams();
    initSpeechRecognition();
    initMonacoEditor();
    initTimer();
    renderQuestion(currentQuestionIndex);
    setupEventListeners();
});

// ================= 1. Media Devices & Waveform Canvas =================
function initMediaStreams() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        aiHintBox.innerHTML = '<span class="text-warning">Media devices not supported in this browser. You can still type your answers.</span>';
        return;
    }

    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then((stream) => {
            mediaStream = stream;
            webcamVideo.srcObject = stream;
            initAudioVisualizer(stream);
        })
        .catch((err) => {
            console.warn("Camera/Mic access not granted:", err);
            aiHintBox.innerHTML = '<span class="text-warning"><i class="bi bi-exclamation-triangle"></i> Camera/Mic access denied. You can proceed with typed responses.</span>';
        });
}

function initAudioVisualizer(stream) {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;

        audioContext = new AudioCtx();
        const source = audioContext.createMediaStreamSource(stream);
        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 64;
        source.connect(analyserNode);

        const canvasCtx = waveformCanvas.getContext('2d');
        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function drawWaveform() {
            animationFrameId = requestAnimationFrame(drawWaveform);
            analyserNode.getByteFrequencyData(dataArray);

            canvasCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
            canvasCtx.fillStyle = '#0f172a';
            canvasCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);

            const barWidth = (waveformCanvas.width / bufferLength) * 2;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * waveformCanvas.height;
                canvasCtx.fillStyle = '#38bdf8';
                canvasCtx.fillRect(x, waveformCanvas.height - barHeight, barWidth - 1, barHeight);
                x += barWidth;
            }
        }
        drawWaveform();
    } catch (e) {
        console.warn("Waveform initialization error:", e);
    }
}

// ================= 2. AI Voice (Text-to-Speech) =================
function speakQuestion(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel(); // Stop prior speech

    aiInterviewerStatus.textContent = "AI Interviewer Speaking...";
    aiInterviewerStatus.className = "text-primary small fw-semibold";

    const cleanStatement = text.replace(/```[\s\S]*?```/g, 'Code snippet omitted for speech.');
    const utterance = new SpeechSynthesisUtterance(cleanStatement);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
        aiInterviewerStatus.textContent = "Listening for candidate answer...";
        aiInterviewerStatus.className = "text-success small fw-semibold";
    };

    utterance.onerror = () => {
        aiInterviewerStatus.textContent = "Ready for response";
        aiInterviewerStatus.className = "text-muted small";
    };

    window.speechSynthesis.speak(utterance);
}

// ================= 3. Speech-to-Text (SpeechRecognition) =================
function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        speechRecognitionStatus.textContent = "Speech recognition not supported in browser. Please type answers.";
        toggleSpeechBtn.disabled = true;
        return;
    }

    speechRecognition = new SpeechRec();
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-US';

    speechRecognition.onstart = () => {
        isRecognizing = true;
        speechBtnText.textContent = "Stop Speaking";
        toggleSpeechBtn.className = "btn btn-sm btn-danger";
        speechRecognitionStatus.innerHTML = '<span class="text-danger fw-semibold"><i class="bi bi-record-circle-fill"></i> Listening... speak your answer.</span>';
    };

    speechRecognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        candidateAnswerInput.value = (candidateAnswerInput.value + ' ' + transcript).trim();
    };

    speechRecognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        if (event.error !== 'no-speech') {
            speechRecognitionStatus.textContent = "Recognition error: " + event.error;
        }
    };

    speechRecognition.onend = () => {
        isRecognizing = false;
        speechBtnText.textContent = "Start Speaking";
        toggleSpeechBtn.className = "btn btn-sm btn-outline-primary";
        speechRecognitionStatus.innerHTML = '<i class="bi bi-info-circle"></i> Microphone ready. Click Start Speaking to record.';
    };
}

function toggleSpeechRecognition() {
    if (!speechRecognition) return;
    if (isRecognizing) {
        speechRecognition.stop();
    } else {
        speechRecognition.start();
    }
}

// ================= 4. Monaco Editor Setup =================
function initMonacoEditor() {
    if (typeof require === 'undefined') return;

    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
        monacoEditorInstance = monaco.editor.create(document.getElementById('monacoEditor'), {
            value: DEFAULT_CODE_SNIPPETS.python,
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
        });
    });
}

// ================= 5. Automatic Question Switching =================
function renderQuestion(index) {
    if (index < 0 || index >= QUESTIONS_LIST.length) return;

    const q = QUESTIONS_LIST[index];

    // Update Header & Progress
    questionTracker.textContent = `${index + 1} / ${TOTAL_QUESTIONS}`;
    const progressPercent = ((index + 1) / TOTAL_QUESTIONS) * 100;
    interviewProgressBar.style.width = `${progressPercent}%`;

    questionStatementText.textContent = q.text;
    questionCategoryBadge.textContent = q.category_display || q.category;
    questionDifficultyBadge.textContent = q.difficulty ? q.difficulty.toUpperCase() : 'INTERMEDIATE';

    // Reset feedback
    instantFeedbackBox.classList.add('d-none');
    candidateAnswerInput.value = q.answer_text || '';

    // AUTOMATIC CODING DETECTION
    if (q.is_coding) {
        // Switch to Monaco Editor
        voiceWorkspaceCard.classList.add('d-none');
        codingWorkspaceCard.classList.remove('d-none');

        const lang = (q.coding_language || 'python').toLowerCase();
        codeLanguageSelect.value = lang;

        const starter = q.starter_code || DEFAULT_CODE_SNIPPETS[lang] || DEFAULT_CODE_SNIPPETS.python;
        if (monacoEditorInstance) {
            monaco.editor.setModelLanguage(monacoEditorInstance.getModel(), lang);
            monacoEditorInstance.setValue(starter);
        }

        consoleOutputArea.textContent = `Problem: ${q.text}\n\nLanguage: ${lang.toUpperCase()}\nWrite your solution and click 'Run Code' or 'Submit Solution'.`;
        executionMetaText.textContent = "Status: Coding Assessment Mode";
    } else {
        // Switch to Voice & Oral Response
        codingWorkspaceCard.classList.add('d-none');
        voiceWorkspaceCard.classList.remove('d-none');
    }

    // Speak Question Aloud
    speakQuestion(q.text);
}

// ================= 6. Event Listeners & Actions =================
function setupEventListeners() {
    // Media Toggles
    toggleCameraBtn.addEventListener('click', () => {
        if (!mediaStream) return;
        const videoTrack = mediaStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.enabled = !videoTrack.enabled;
            cameraIcon.className = videoTrack.enabled ? "bi bi-camera-video-fill" : "bi bi-camera-video-off-fill text-danger";
        }
    });

    toggleMicBtn.addEventListener('click', () => {
        if (!mediaStream) return;
        const audioTrack = mediaStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = !audioTrack.enabled;
            micIcon.className = audioTrack.enabled ? "bi bi-mic-fill" : "bi bi-mic-mute-fill text-danger";
        }
    });

    repeatQuestionBtn.addEventListener('click', () => {
        const q = QUESTIONS_LIST[currentQuestionIndex];
        speakQuestion(q.text);
    });

    stopSpeechBtn.addEventListener('click', () => {
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        aiInterviewerStatus.textContent = "AI voice muted.";
    });

    toggleSpeechBtn.addEventListener('click', toggleSpeechRecognition);
    clearAnswerBtn.addEventListener('click', () => { candidateAnswerInput.value = ''; });

    // Submit Oral Answer
    submitOralAnswerBtn.addEventListener('click', submitOralAnswer);

    // Code Language Selection
    codeLanguageSelect.addEventListener('change', (e) => {
        const selectedLang = e.target.value;
        if (monacoEditorInstance) {
            monaco.editor.setModelLanguage(monacoEditorInstance.getModel(), selectedLang);
            monacoEditorInstance.setValue(DEFAULT_CODE_SNIPPETS[selectedLang] || '');
        }
    });

    // Run Code Sandbox Action
    runCodeBtn.addEventListener('click', executeCodeSandbox);

    // Submit Code Solution
    submitCodeBtn.addEventListener('click', submitCodeSolution);

    // End Interview
    finishInterviewBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to finish the interview and generate your performance report?")) {
            finishInterview();
        }
    });
}

// ================= 7. Submit Handlers =================
function submitOralAnswer() {
    const q = QUESTIONS_LIST[currentQuestionIndex];
    const answer = candidateAnswerInput.value.trim();

    if (!answer) {
        alert("Please provide an answer verbally or type in the response area before submitting.");
        return;
    }

    if (speechRecognition && isRecognizing) speechRecognition.stop();

    submitOralAnswerBtn.disabled = true;
    submitOralAnswerBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Evaluating...';

    fetch(`/api/interview/${SESSION_ID}/submit-answer/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            question_id: q.id,
            answer_text: answer,
            is_audio: true
        })
    })
    .then(res => res.json())
    .then(data => {
        submitOralAnswerBtn.disabled = false;
        submitOralAnswerBtn.innerHTML = '<i class="bi bi-send-fill me-1"></i> Submit Answer & Next';

        // Display brief evaluation feedback
        instantFeedbackBox.classList.remove('d-none');
        feedbackScore.textContent = `Score: ${data.score}/10`;
        feedbackStrengths.innerHTML = `<strong>Feedback:</strong> ${data.strengths}`;
        feedbackFollowUp.innerHTML = data.follow_up ? `<strong>Follow-Up:</strong> ${data.follow_up}` : '';

        // Auto advance after 2.5 seconds or immediately if last question
        setTimeout(() => {
            advanceQuestion();
        }, 2200);
    })
    .catch(err => {
        submitOralAnswerBtn.disabled = false;
        submitOralAnswerBtn.innerHTML = '<i class="bi bi-send-fill me-1"></i> Submit Answer & Next';
        console.error("Submission failed:", err);
        advanceQuestion();
    });
}

function executeCodeSandbox() {
    const q = QUESTIONS_LIST[currentQuestionIndex];
    const code = monacoEditorInstance ? monacoEditorInstance.getValue() : '';
    const lang = codeLanguageSelect.value;

    runCodeBtn.disabled = true;
    runCodeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Running...';
    executionMetaText.textContent = "Status: Executing in Sandbox...";
    consoleOutputArea.textContent = "Sending code to execution sandbox...";

    fetch(`/api/interview/${SESSION_ID}/run-code/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            question_id: q.id,
            source_code: code,
            language: lang
        })
    })
    .then(res => res.json())
    .then(data => {
        runCodeBtn.disabled = false;
        runCodeBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Code';
        executionMetaText.textContent = `Status: ${data.status} | Passed: ${data.passed_test_cases}/${data.total_test_cases} | Time: ${data.execution_time}s`;

        let output = `[EXECUTION RESULT - ${data.status.toUpperCase()}]\n`;
        if (data.stdout) output += `STDOUT:\n${data.stdout}\n`;
        if (data.stderr) output += `STDERR:\n${data.stderr}\n`;
        if (data.compile_output) output += `COMPILE:\n${data.compile_output}\n`;
        consoleOutputArea.textContent = output;
    })
    .catch(err => {
        runCodeBtn.disabled = false;
        runCodeBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Code';
        consoleOutputArea.textContent = "Execution request failed: " + err;
    });
}

function submitCodeSolution() {
    const q = QUESTIONS_LIST[currentQuestionIndex];
    const code = monacoEditorInstance ? monacoEditorInstance.getValue() : '';
    const lang = codeLanguageSelect.value;

    submitCodeBtn.disabled = true;
    submitCodeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Submitting...';

    fetch(`/api/interview/${SESSION_ID}/submit-code/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
            question_id: q.id,
            source_code: code,
            language: lang
        })
    })
    .then(res => res.json())
    .then(data => {
        submitCodeBtn.disabled = false;
        submitCodeBtn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Submit Solution';
        alert(`Solution evaluated! Score: ${data.score}/10 (${data.passed}/${data.total} test cases passed).\n\nAI Feedback: ${data.feedback}`);
        advanceQuestion();
    })
    .catch(err => {
        submitCodeBtn.disabled = false;
        submitCodeBtn.innerHTML = '<i class="bi bi-check-circle-fill"></i> Submit Solution';
        console.error("Submission failed:", err);
        advanceQuestion();
    });
}

function advanceQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < QUESTIONS_LIST.length) {
        renderQuestion(currentQuestionIndex);
    } else {
        finishInterview();
    }
}

function finishInterview() {
    clearInterval(timerInterval);
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }

    aiInterviewerStatus.textContent = "Finalizing performance evaluation...";

    fetch(`/api/interview/${SESSION_ID}/finish/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.report_url) {
            window.location.href = data.report_url;
        } else {
            window.location.href = `/interview/${SESSION_ID}/report/`;
        }
    })
    .catch(err => {
        window.location.href = `/interview/${SESSION_ID}/report/`;
    });
}

// ================= 8. Countdown Timer =================
function initTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        timerSecondsRemaining--;
        updateTimerDisplay();
        if (timerSecondsRemaining <= 0) {
            clearInterval(timerInterval);
            alert("Interview time has expired. Generating your performance report.");
            finishInterview();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timerSecondsRemaining / 60);
    const seconds = timerSecondsRemaining % 60;
    sessionTimerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
