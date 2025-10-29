let player;
let bookmarks = [];
const filename = document.getElementById('mediaPlayer').dataset.filename;

document.addEventListener('DOMContentLoaded', function() {
    player = videojs('mediaPlayer', {
        controls: true,
        fluid: true,
        preload: 'auto',
        playbackRates: [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
    });

    loadPlayerSettings();
    loadBookmarks();
    setupEventListeners();
    
    player.on('play', function() {
        updateAnalytics('play');
    });

    player.on('pause', function() {
        savePlaybackPosition();
    });

    player.on('timeupdate', function() {
        if (Math.floor(player.currentTime()) % 10 === 0) {
            savePlaybackPosition();
        }
    });

    player.on('ended', function() {
        updateAnalytics('ended', player.currentTime());
    });

    const savedPosition = getSavedPosition();
    if (savedPosition > 0 && localStorage.getItem('rememberPosition') === 'true') {
        player.currentTime(savedPosition);
    }

    if (localStorage.getItem('autoplay') === 'true') {
        player.play();
    }
});

function loadPlayerSettings() {
    const speed = parseFloat(localStorage.getItem('defaultSpeed') || '1');
    const volume = parseInt(localStorage.getItem('defaultVolume') || '80') / 100;
    
    player.playbackRate(speed);
    player.volume(volume);
    
    document.getElementById('speedControl').value = speed;
}

function setupEventListeners() {
    document.getElementById('speedControl').addEventListener('change', function() {
        player.playbackRate(parseFloat(this.value));
    });

    document.getElementById('loopToggle').addEventListener('change', function() {
        player.loop(this.checked);
    });

    document.getElementById('autoplayToggle').addEventListener('change', function() {
        player.autoplay(this.checked);
    });

    document.getElementById('pipBtn').addEventListener('click', async function() {
        try {
            if (document.pictureInPictureElement) {
                await document.exitPictureInPicture();
            } else {
                await player.el().querySelector('video').requestPictureInPicture();
            }
        } catch (error) {
            alert('Picture-in-Picture not supported or failed');
        }
    });

    document.getElementById('screenshotBtn').addEventListener('click', function() {
        takeScreenshot();
    });

    document.getElementById('addBookmarkBtn').addEventListener('click', function() {
        addBookmark();
    });

    document.getElementById('uploadSubtitleBtn').addEventListener('click', function() {
        uploadSubtitle();
    });
}

function savePlaybackPosition() {
    const position = player.currentTime();
    localStorage.setItem(`position_${filename}`, position.toString());
}

function getSavedPosition() {
    return parseFloat(localStorage.getItem(`position_${filename}`) || '0');
}

async function updateAnalytics(eventType, watchTime = 0) {
    try {
        await fetch('/update_analytics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: filename,
                event_type: eventType,
                watch_time: watchTime
            })
        });
    } catch (error) {
        console.error('Analytics update failed:', error);
    }
}

function takeScreenshot() {
    const video = player.el().querySelector('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(function(blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `screenshot_${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(url);
    });
}

function addBookmark() {
    const time = player.currentTime();
    const name = prompt('Bookmark name:', `Bookmark at ${formatTime(time)}`);
    
    if (name) {
        bookmarks.push({ time: time, name: name });
        saveBookmarks();
        displayBookmarks();
    }
}

function loadBookmarks() {
    const saved = localStorage.getItem(`bookmarks_${filename}`);
    if (saved) {
        bookmarks = JSON.parse(saved);
        displayBookmarks();
    }
}

function saveBookmarks() {
    localStorage.setItem(`bookmarks_${filename}`, JSON.stringify(bookmarks));
}

function displayBookmarks() {
    const container = document.getElementById('bookmarksList');
    container.innerHTML = '';
    
    if (bookmarks.length === 0) {
        container.innerHTML = '<p class="text-muted">No bookmarks yet</p>';
        return;
    }
    
    bookmarks.forEach((bookmark, index) => {
        const div = document.createElement('div');
        div.className = 'd-flex justify-content-between align-items-center mb-2 p-2 border rounded';
        div.innerHTML = `
            <div>
                <strong>${bookmark.name}</strong><br>
                <small class="text-muted">${formatTime(bookmark.time)}</small>
            </div>
            <div>
                <button class="btn btn-sm btn-primary me-1" onclick="jumpToBookmark(${index})">
                    <i class="bi bi-play-fill"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteBookmark(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

function jumpToBookmark(index) {
    player.currentTime(bookmarks[index].time);
    player.play();
}

function deleteBookmark(index) {
    bookmarks.splice(index, 1);
    saveBookmarks();
    displayBookmarks();
}

async function uploadSubtitle() {
    const fileInput = document.getElementById('subtitleFile');
    const langInput = document.getElementById('subtitleLang');
    
    if (!fileInput.files[0]) {
        alert('Please select a subtitle file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('media_id', new URLSearchParams(window.location.search).get('file'));
    formData.append('language', langInput.value || 'unknown');
    
    try {
        const response = await fetch('/upload_subtitle', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Subtitle uploaded successfully!');
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }
}
