function setupRecorder(recordButtonId, stopButtonId, audioPreviewId, recordedAudioInputId) {
    const recordButton = document.getElementById(recordButtonId);
    const stopButton = document.getElementById(stopButtonId);
    const audioPreview = document.getElementById(audioPreviewId);
    const recordedAudioInput = document.getElementById(recordedAudioInputId);
    let mediaRecorder;
    let audioChunks = [];

    recordButton.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
                const audioUrl = URL.createObjectURL(audioBlob);
                audioPreview.src = audioUrl;
                audioPreview.hidden = false;

                const file = new File([audioBlob], `recording_${Date.now()}.mp3`, { type: 'audio/mp3' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                recordedAudioInput.files = dataTransfer.files;
            };

            mediaRecorder.start();
            recordButton.disabled = true;
            stopButton.disabled = false;
        } catch (err) {
            console.error('Erreur d’accès au microphone:', err);
            alert('Impossible d’accéder au microphone. Vérifiez les permissions.');
        }
    });

    stopButton.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            recordButton.disabled = false;
            stopButton.disabled = true;
        }
    });
}

// Initialisation pour submit_request
if (document.getElementById('recordButton')) {
    setupRecorder('recordButton', 'stopButton', 'audioPreview', 'recordedAudio');
}

// Initialisation pour messages
if (document.getElementById('messageRecordButton')) {
    setupRecorder('messageRecordButton', 'messageStopButton', 'messageAudioPreview', 'messageRecordedAudio');
}