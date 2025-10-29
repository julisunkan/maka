
let mediaRecorder;
let recordedChunks = [];
let stream;
let recordingStartTime;
let recordingTimer;
let audioContext;
let analyser;
let animationId;

const preview = document.getElementById('preview');
const playback = document.getElementById('playback');
const visualizer = document.getElementById('visualizer');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const pauseBtn = document.getElementById('pauseBtn');
const uploadBtn = document.getElementById('uploadBtn');
const discardBtn = document.getElementById('discardBtn');
const playbackCard = document.getElementById('playbackCard');
const recordingTime = document.getElementById('recordingTime');
const recordingIndicator = document.getElementById('recordingIndicator');
const videoMode = document.getElementById('videoMode');

function showRecorderNotification(message, type = 'info') {
    if (typeof showNotification === 'function') {
        showNotification(message, type);
    } else {
        const container = document.getElementById('notificationContainer');
        if (!container) return;
        
        const alertTypes = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };
        
        const alertClass = alertTypes[type] || 'alert-info';
        
        const alert = document.createElement('div');
        alert.className = `alert ${alertClass} alert-dismissible fade show mb-2`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        container.appendChild(alert);
        
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    }
}

const audioMode = document.getElementById('audioMode');

function updateRecordingTime() {
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;
    recordingTime.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function drawVisualizer() {
    if (!analyser) return;
    
    const canvas = visualizer;
    const canvasCtx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    function draw() {
        animationId = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);
        
        canvasCtx.fillStyle = 'rgb(0, 0, 0)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
        
        const barWidth = (canvas.width / bufferLength) * 2.5;
        let barHeight;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height;
            
            canvasCtx.fillStyle = `rgb(${barHeight + 100}, 50, 50)`;
            canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
        }
    }
    
    draw();
}

async function startRecording() {
    const isVideoMode = videoMode.checked;
    
    try {
        const constraints = isVideoMode
            ? { video: true, audio: true }
            : { audio: true };
        
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        
        if (isVideoMode) {
            preview.srcObject = stream;
            preview.classList.remove('d-none');
            visualizer.classList.add('d-none');
        } else {
            preview.classList.add('d-none');
            visualizer.classList.remove('d-none');
            
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 256;
            
            drawVisualizer();
        }
        
        const options = { mimeType: 'video/webm;codecs=vp9' };
        mediaRecorder = new MediaRecorder(stream, options);
        
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            playback.src = URL.createObjectURL(blob);
            playbackCard.classList.remove('d-none');
            
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
        };
        
        mediaRecorder.start();
        recordingStartTime = Date.now();
        recordingTimer = setInterval(updateRecordingTime, 1000);
        
        startBtn.classList.add('d-none');
        stopBtn.classList.remove('d-none');
        pauseBtn.classList.remove('d-none');
        recordingIndicator.classList.remove('d-none');
        
        showRecorderNotification('Recording started', 'success');
        
    } catch (error) {
        showRecorderNotification('Error accessing media devices: ' + error.message, 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearInterval(recordingTimer);
        
        startBtn.classList.remove('d-none');
        stopBtn.classList.add('d-none');
        pauseBtn.classList.add('d-none');
        recordingIndicator.classList.add('d-none');
        
        recordingTime.textContent = '00:00:00';
        
        showRecorderNotification('Recording stopped', 'info');
    }
}

function pauseRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.pause();
        pauseBtn.innerHTML = '<i class="bi bi-play-circle"></i> Resume';
        showRecorderNotification('Recording paused', 'info');
    } else if (mediaRecorder && mediaRecorder.state === 'paused') {
        mediaRecorder.resume();
        pauseBtn.innerHTML = '<i class="bi bi-pause-circle"></i> Pause';
        showRecorderNotification('Recording resumed', 'info');
    }
}

async function downloadRecording() {
    if (recordedChunks.length === 0) {
        showRecorderNotification('No recording to download', 'warning');
        return;
    }
    
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `recording_${videoMode.checked ? 'video' : 'audio'}_${timestamp}.webm`;
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
    
    showRecorderNotification('Recording downloaded successfully!', 'success');
    
    // Clear the recording after download
    setTimeout(() => {
        discardRecording();
    }, 1000);
}

function discardRecording() {
    recordedChunks = [];
    playback.src = '';
    playbackCard.classList.add('d-none');
    showRecorderNotification('Recording discarded', 'info');
}

startBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);
pauseBtn.addEventListener('click', pauseRecording);
uploadBtn.addEventListener('click', downloadRecording);
discardBtn.addEventListener('click', discardRecording);

videoMode.addEventListener('change', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});

audioMode.addEventListener('change', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});
