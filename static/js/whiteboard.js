/**
 * Real-time Collaborative Whiteboard Logic
 * Syncs drawing strokes to all group members via Socket.IO
 */
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('whiteboard');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const group_id = typeof GROUP_ID !== 'undefined' ? GROUP_ID : null;
    if (!group_id) return;

    // Re-use the socket already created by group_chat.js if available,
    // otherwise create a new one. This avoids double connections.
    const socket = window._groupSocket || io('/', { transports: ['websocket', 'polling'] });

    // Join the group room (matching format used by group chat)
    socket.emit('join', { group_id: group_id });

    // ---------------------------------------------------------------
    // State
    // ---------------------------------------------------------------
    let drawing = false;
    let last = { x: 0, y: 0 };
    let penColor = '#000000';
    let penSize = 2;

    // ---------------------------------------------------------------
    // Controls
    // ---------------------------------------------------------------
    const colorPicker = document.getElementById('wb-color');
    const sizePicker = document.getElementById('wb-size');
    const clearBtn = document.getElementById('wb-clear');
    const saveBtn = document.getElementById('wb-save');

    if (colorPicker) {
        colorPicker.addEventListener('input', (e) => penColor = e.target.value);
        penColor = colorPicker.value;
    }
    if (sizePicker) {
        sizePicker.addEventListener('input', (e) => penSize = parseInt(e.target.value));
        penSize = parseInt(sizePicker.value);
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            clearCanvas();
            socket.emit('wb_clear', { room: group_id });
        });
    }
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const link = document.createElement('a');
            link.download = `whiteboard-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
        });
    }

    // ---------------------------------------------------------------
    // Resize canvas to fill its container (called once + on tab switch)
    // ---------------------------------------------------------------
    function resizeCanvas() {
        const parent = canvas.parentElement;
        // Preserve drawn content by copying to a temp image
        const img = new Image();
        img.src = canvas.toDataURL();
        canvas.width = parent.clientWidth || 800;
        canvas.height = parent.clientHeight || 500;
        img.onload = () => ctx.drawImage(img, 0, 0);
    }

    // Delay initial resize so the tab content is visible and has dimensions
    setTimeout(resizeCanvas, 100);
    window.addEventListener('resize', resizeCanvas);

    // Called by switchTab() in the template when whiteboard becomes visible
    window.triggerWhiteboardResize = function () {
        setTimeout(resizeCanvas, 60);
    };

    // ---------------------------------------------------------------
    // Drawing helpers
    // ---------------------------------------------------------------
    function drawSegment(x0, y0, x1, y1, color, size) {
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.strokeStyle = color;
        ctx.lineWidth = size;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();
        ctx.closePath();
    }

    function emitDraw(x0, y0, x1, y1) {
        socket.emit('wb_draw', {
            room: group_id,
            // Normalise to 0-1 so it works on canvases of different sizes
            x0: x0 / canvas.width,
            y0: y0 / canvas.height,
            x1: x1 / canvas.width,
            y1: y1 / canvas.height,
            color: penColor,
            size: penSize
        });
    }

    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    // ---------------------------------------------------------------
    // Mouse events
    // ---------------------------------------------------------------
    canvas.addEventListener('mousedown', (e) => {
        drawing = true;
        last.x = e.offsetX;
        last.y = e.offsetY;
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!drawing) return;
        const nx = e.offsetX, ny = e.offsetY;
        drawSegment(last.x, last.y, nx, ny, penColor, penSize);
        emitDraw(last.x, last.y, nx, ny);
        last.x = nx;
        last.y = ny;
    });

    canvas.addEventListener('mouseup', (e) => {
        if (!drawing) return;
        drawing = false;
        drawSegment(last.x, last.y, e.offsetX, e.offsetY, penColor, penSize);
        emitDraw(last.x, last.y, e.offsetX, e.offsetY);
    });

    canvas.addEventListener('mouseleave', () => {
        drawing = false;
    });

    // ---------------------------------------------------------------
    // Touch events
    // ---------------------------------------------------------------
    function getTouchPos(touch) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: (touch.clientX - rect.left) * (canvas.width / rect.width),
            y: (touch.clientY - rect.top) * (canvas.height / rect.height)
        };
    }

    canvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        drawing = true;
        const pos = getTouchPos(e.touches[0]);
        last.x = pos.x;
        last.y = pos.y;
    }, { passive: false });

    canvas.addEventListener('touchmove', (e) => {
        e.preventDefault();
        if (!drawing) return;
        const pos = getTouchPos(e.touches[0]);
        drawSegment(last.x, last.y, pos.x, pos.y, penColor, penSize);
        emitDraw(last.x, last.y, pos.x, pos.y);
        last.x = pos.x;
        last.y = pos.y;
    }, { passive: false });

    canvas.addEventListener('touchend', () => {
        drawing = false;
    });

    // ---------------------------------------------------------------
    // Socket.IO listeners — receive remote drawing events
    // ---------------------------------------------------------------
    socket.on('wb_draw', (data) => {
        const x0 = data.x0 * canvas.width;
        const y0 = data.y0 * canvas.height;
        const x1 = data.x1 * canvas.width;
        const y1 = data.y1 * canvas.height;
        drawSegment(x0, y0, x1, y1, data.color, data.size);
    });

    socket.on('wb_clear', () => {
        clearCanvas();
    });
});
