
/* ========================================
   CALENDAR & EVENT LOGIC
   ======================================== */
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Global State ---
    const today = new Date();
    let currentMonth = today.getMonth(); // 0-11
    let currentYear = today.getFullYear();
    let selectedDate = formatDate(today); // "YYYY-MM-DD"

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

    // Elements
    const monthLabel = document.querySelector('.cal-header span');
    const dayGrid = document.querySelector('.cal-days-grid');
    const prevBtn = document.querySelector('.cal-nav-btn:first-child');
    const nextBtn = document.querySelector('.cal-nav-btn:last-child');
    const timelineInfo = document.querySelector('.timeline-info');
    const eventListContainer = document.getElementById('eventListContainer');
    const initEventBtn = document.querySelector('.btn-init-event');

    // --- 2. Helper Functions ---
    function formatDate(date) {
        // Returns YYYY-MM-DD local
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function renderCalendar(month, year) {
        // Update header
        monthLabel.textContent = `${monthNames[month]} ${year}`;

        // Clear old days (keep labels)
        const labels = Array.from(dayGrid.children).slice(0, 7);
        dayGrid.innerHTML = '';
        labels.forEach(l => dayGrid.appendChild(l));

        const firstDay = new Date(year, month, 1).getDay(); // 0 (Sun) - 6 (Sat)
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        // Empty slots for previous month
        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'cal-day empty';
            dayGrid.appendChild(empty);
        }

        // Days
        for (let d = 1; d <= daysInMonth; d++) {
            const cell = document.createElement('div');
            cell.className = 'cal-day';
            cell.textContent = d;

            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            cell.dataset.date = dateStr;

            if (dateStr === selectedDate) {
                cell.classList.add('active');
            }

            // Interaction
            cell.addEventListener('click', () => {
                document.querySelectorAll('.cal-day.active').forEach(el => el.classList.remove('active'));
                cell.classList.add('active');
                selectedDate = dateStr;
                updateTimelineForDate(dateStr);
            });

            dayGrid.appendChild(cell);
        }
    }

    function updateTimelineForDate(dateStr) {
        // Update header info "Timeline // Jan 25"
        const d = new Date(dateStr);
        const parts = dateStr.split('-');
        const displayDate = new Date(parts[0], parts[1] - 1, parts[2]);

        const dayName = displayDate.toLocaleString('default', { month: 'short', day: 'numeric' });
        timelineInfo.innerHTML = `<i class="fa-regular fa-clock"></i> Timeline // ${dayName}`;

        // Fetch events from API
        eventListContainer.innerHTML = `<div style="padding: 20px; text-align: center;"><i class="fa-solid fa-spinner fa-spin"></i></div>`;

        fetch(`/api/events?date=${dateStr}`)
            .then(r => r.json())
            .then(data => {
                const events = data.events;
                if (events.length === 0) {
                    eventListContainer.innerHTML = `
                        <div class="event-placeholder" id="eventPlaceholder">
                            <i class="fa-regular fa-clock"></i>
                            <div style="font-size: 0.85rem; font-weight: 600;">Zero Collisions Detected</div>
                            <div style="font-size: 0.7rem;">No scheduled events for today</div>
                        </div>
                    `;
                } else {
                    let html = `<div style="display: flex; flex-direction: column; gap: 10px; width: 100%;">`;
                    events.forEach(e => {
                        html += `
                            <div class="event-item" style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 12px; border-left: 3px solid var(--accent-green); position: relative; group;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-right: 60px;">
                                    <div>
                                        <div style="font-weight: 700; color: #fff;">${e.title}</div>
                                        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">${e.description}</div>
                                    </div>
                                    <div style="font-size: 0.75rem; color: var(--accent-green); font-weight: 700;">${e.time || ''}</div>
                                </div>
                                <div class="event-actions" style="position: absolute; right: 10px; top: 12px; display: flex; gap: 8px;">
                                    <i class="fa-solid fa-pen-to-square" onclick="editEvent(${JSON.stringify(e).replace(/"/g, '&quot;')})" style="cursor: pointer; color: #888; font-size: 0.85rem; transition: 0.3s;" onmouseover="this.style.color='var(--accent-green)'" onmouseout="this.style.color='#888'"></i>
                                    <i class="fa-solid fa-trash-can" onclick="deleteEvent(${e.id})" style="cursor: pointer; color: #888; font-size: 0.85rem; transition: 0.3s;" onmouseover="this.style.color='#ef4444'" onmouseout="this.style.color='#888'"></i>
                                </div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                    eventListContainer.innerHTML = html;
                }
            });
    }

    function editEvent(event) {
        document.getElementById('editEventId').value = event.id;
        document.getElementById('eventModalTitle').textContent = 'Edit Event';
        document.getElementById('btnSaveEvent').textContent = 'Update Event';

        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventDescription').value = event.description;
        document.getElementById('eventTime').value = event.time;

        document.getElementById('createEventModal').style.display = 'flex';
    }

    function deleteEvent(eventId) {
        if (!confirm("Are you sure you want to delete this event?")) return;

        fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    updateTimelineForDate(selectedDate);
                }
            });
    }

    function openCreateEventModal() {
        document.getElementById('editEventId').value = '';
        document.getElementById('eventModalTitle').textContent = 'Initialize Event';
        document.getElementById('btnSaveEvent').textContent = 'Initialize Event';

        document.getElementById('createEventModal').style.display = 'flex';
        document.getElementById('eventTitle').value = '';
        document.getElementById('eventDescription').value = '';

        // Default to current time
        const now = new Date();
        const currentTime = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');
        document.getElementById('eventTime').value = currentTime;
    }

    function saveEvent() {
        const title = document.getElementById('eventTitle').value;
        const desc = document.getElementById('eventDescription').value;
        const time = document.getElementById('eventTime').value;
        const editId = document.getElementById('editEventId').value;

        if (!title) {
            alert("Title is required");
            return;
        }

        const url = editId ? `/api/events/${editId}` : '/api/events';
        const method = editId ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                description: desc,
                date: selectedDate,
                time: time
            })
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('createEventModal').style.display = 'none';
                    updateTimelineForDate(selectedDate);
                } else {
                    alert("Failed to save event");
                }
            })
            .catch(err => {
                console.error("Save error:", err);
                alert("An error occurred while saving the event.");
            });
    }

    // Assign to window AFTER they are defined (though hoisting handles it anyway)
    window.openCreateEventModal = openCreateEventModal;
    window.saveEvent = saveEvent;
    window.editEvent = editEvent;
    window.deleteEvent = deleteEvent;

    // --- 4. Event Reminder Popup Check ---
    function checkReminders() {
        fetch('/api/events/check-warnings')
            .then(r => r.json())
            .then(data => {
                if (data.has_warning && data.event) {
                    showEventPopup(data.event);
                }
            });
    }

    function showEventPopup(event) {
        // Create custom modal matching system UI
        const modalId = 'event-popup-' + event.id;
        if (document.getElementById(modalId)) return; // already showing

        // Optional: Play a soft notification sound
        try {
            const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2857/2857-preview.mp3');
            audio.volume = 0.5;
            audio.play().catch(e => console.log("Audio play blocked"));
        } catch (e) { }

        // Format time for display (24h to 12h)
        let displayTime = event.time;
        try {
            if (event.time && event.time.includes(':')) {
                let [h, m] = event.time.split(':');
                let hh = parseInt(h);
                let ampm = hh >= 12 ? 'PM' : 'AM';
                hh = hh % 12 || 12;
                displayTime = `${hh}:${m} ${ampm}`;
            }
        } catch (e) { }

        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal-overlay';
        modal.style.display = 'flex';
        modal.style.background = 'rgba(0,0,0,0.85)';
        modal.style.zIndex = '3000';
        modal.style.backdropFilter = 'blur(10px)';

        modal.innerHTML = `
            <div class="modal-content" style="background: linear-gradient(135deg, #111 0%, #0a0a0a 100%); border: 1px solid rgba(74, 222, 128, 0.3); padding: 40px; border-radius: 24px; width: 420px; text-align: center; position: relative; box-shadow: 0 0 60px rgba(74, 222, 128, 0.15); animation: popupReveal 0.5s cubic-bezier(0.16, 1, 0.3, 1);">
                
                <div style="background: linear-gradient(45deg, rgba(74, 222, 128, 0.1), rgba(74, 222, 128, 0.05)); width: 80px; height: 80px; border-radius: 50%; border: 1px solid rgba(74, 222, 128, 0.5); display: grid; place-items: center; margin: 0 auto 24px; box-shadow: 0 0 20px rgba(74, 222, 128, 0.1); animation: pulseGreen 2s infinite;">
                    <i class="fa-solid fa-bolt-lightning" style="font-size: 2rem; color: var(--accent-green);"></i>
                </div>

                <div style="text-transform: uppercase; letter-spacing: 2px; font-size: 0.75rem; color: var(--accent-green); font-weight: 800; margin-bottom: 12px;">Active Event Arrived</div>
                
                <h2 style="color: #fff; font-family: var(--font-heading); font-size: 1.8rem; margin-bottom: 15px; font-weight: 800; line-height: 1.2;">${event.title}</h2>
                
                <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 8px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                    <i class="fa-regular fa-clock" style="color: var(--accent-green);"></i>
                    <span style="color: #fff; font-weight: 600; font-size: 0.9rem;">${displayTime || 'All Day'}</span>
                </div>

                <div style="color: var(--text-secondary); margin-bottom: 30px; font-size: 1rem; line-height: 1.6; min-height: 50px;">
                    ${event.description || 'It\'s time for your scheduled event!'}
                </div>
                
                <button id="btn-dismiss-${event.id}" class="btn-primary" style="width: 100%; padding: 16px; border-radius: 14px; background: var(--accent-green); color: #000; font-weight: 800; border: none; cursor: pointer; font-size: 1rem; box-shadow: 0 4px 15px rgba(74, 222, 128, 0.2); transition: all 0.3s ease;">
                    Dismis & Acknowledge
                </button>

                <style>
                    @keyframes popupReveal {
                        from { opacity: 0; transform: scale(0.9) translateY(20px); }
                        to { opacity: 1; transform: scale(1) translateY(0); }
                    }
                    @keyframes pulseGreen {
                        0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }
                        70% { box-shadow: 0 0 0 20px rgba(74, 222, 128, 0); }
                        100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
                    }
                    #btn-dismiss-${event.id}:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 6px 20px rgba(74, 222, 128, 0.3);
                        filter: brightness(1.1);
                    }
                </style>
            </div>
        `;

        document.body.appendChild(modal);

        // Dismiss Logic
        document.getElementById(`btn-dismiss-${event.id}`).addEventListener('click', () => {
            fetch(`/api/events/${event.id}/dismiss`, { method: 'POST' })
                .then(() => {
                    modal.style.opacity = '0';
                    modal.style.transition = 'opacity 0.3s ease';
                    setTimeout(() => modal.remove(), 300);
                });
        });
    }

    // --- 5. Initializers ---
    renderCalendar(currentMonth, currentYear);
    updateTimelineForDate(selectedDate); // Load today's events initially
    checkReminders(); // Check for warnings on load

    // Poll for reminders every 15 seconds
    setInterval(checkReminders, 15000);

    // Listeners
    prevBtn.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
        renderCalendar(currentMonth, currentYear);
    });

    nextBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
        renderCalendar(currentMonth, currentYear);
    });

    // Event listener removed as we use onclick="openCreateEventModal()" in HTML to avoid scope issues.
    // initEventBtn.addEventListener('click', openCreateEventModal);
});
