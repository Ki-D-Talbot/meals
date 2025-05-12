// calendar.js - Calendar page functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get meals from Flask template via data attribute
    var mealDataElement = document.getElementById('meal-data');
    var meals = [];    if (mealDataElement) {
        try {
            meals = JSON.parse(mealDataElement.getAttribute('data-meals'));
            console.log(`Loaded ${meals.length} meals for the calendar`);
        } catch (e) {
            console.error("Error parsing meals data:", e);
            meals = []; // Use empty array if there's an error
        }
    } else {
        console.error("Meal data element not found in DOM!");
    }
    
    // Calendar initialization
    var calendarEl = document.getElementById('calendar');
    var dateSelected = '';
    var currentMealId = null; // Track if we're editing an existing meal    var isEditing = false;
    var mealText = '';
    var mealType = 'other';
    
    // Check if FullCalendar is available
    if (typeof FullCalendar === 'undefined') {
        console.error("FullCalendar library not loaded! Please check your network connection or script includes.");
        if (calendarEl) {
            calendarEl.innerHTML = 
                "<div class='alert alert-danger'>Calendar could not be loaded. Please refresh the page or check your internet connection.</div>";
        }
        return;
    }
    
    if (!calendarEl) {
        console.error("Calendar element not found in the DOM");
        return;
    }
      try {
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            events: meals,
            selectable: true, // Enable date selection/clicking
            eventClick: function(info) {
                // Show edit modal when clicking an existing meal                currentMealId = info.event.id;
                isEditing = true;
                dateSelected = info.event.startStr;
                document.getElementById('selectedDate').textContent = formatDate(dateSelected);
                document.getElementById('mealDescription').value = info.event.title;
                
                // Safely access extendedProps
                var mealType = 'other';
                if (info.event.extendedProps && info.event.extendedProps.meal_type) {
                    mealType = info.event.extendedProps.meal_type;
                }
                document.getElementById('mealType').value = mealType;
                
                // Change modal title and button text for editing
                document.querySelector('.meal-modal-header h3').textContent = 'Edit Meal for ' + formatDate(dateSelected);
                document.getElementById('saveMeal').textContent = 'Update Meal';
                
                // Show delete button
                document.getElementById('deleteMeal').style.display = 'block';                // Show the modal
                var modal = document.getElementById('mealModal');
                if (modal) {
                    modal.style.display = 'flex';
                    console.log("Modal display set to flex");
                } else {
                    console.error("Modal element not found!");
                }
                document.getElementById('mealDescription').focus();
            },            dateClick: function(info) {
                // Show modal for adding a new meal
                console.log("Date clicked:", info.dateStr);
                dateSelected = info.dateStr;
                isEditing = false;
                currentMealId = null;
                
                // Reset the form
                var mealDescriptionEl = document.getElementById('mealDescription');
                var mealTypeEl = document.getElementById('mealType');
                var saveBtnEl = document.getElementById('saveMeal');
                var deleteBtnEl = document.getElementById('deleteMeal');
                var selectedDateEl = document.getElementById('selectedDate');
                var modalHeaderTitle = document.querySelector('.meal-modal-header h3');
                
                if (mealDescriptionEl) mealDescriptionEl.value = '';
                if (mealTypeEl) mealTypeEl.value = 'other';
                
                // Change modal title and button text for adding
                if (modalHeaderTitle) modalHeaderTitle.textContent = 'Add Meal for ' + formatDate(dateSelected);
                if (saveBtnEl) saveBtnEl.textContent = 'Save Meal';
                
                // Hide delete button
                if (deleteBtnEl) deleteBtnEl.style.display = 'none';
                
                // Show the modal
                if (selectedDateEl) selectedDateEl.textContent = formatDate(dateSelected);
                var modal = document.getElementById('mealModal');
                if (modal) {
                    modal.style.display = 'flex';
                    console.log("Modal display set to flex for dateClick");
                } else {
                    console.error("Modal element not found in dateClick!");
                }
                
                // Focus on the input field if it exists
                if (mealDescriptionEl) mealDescriptionEl.focus();
            }
        });
        
        calendar.render();
        console.log("Calendar successfully rendered");
    } catch (e) {
        console.error("Error creating or rendering calendar:", e);
        calendarEl.innerHTML = 
            "<div class='alert alert-danger'>Error initializing calendar: " + e.message + "</div>";
    }
    
    // Register event handlers
    function registerEventHandlers() {
        console.log("Registering event handlers");
          // Modal functionality
        var cancelBtn = document.getElementById('cancelMeal');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                closeModal();
            });
        }
        
        var closeBtn = document.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                closeModal();
            });
        }
        
        var saveBtn = document.getElementById('saveMeal');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                saveMeal();
            });
        }
        
        var deleteBtn = document.getElementById('deleteMeal');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this meal?')) {
                    deleteMeal();
                }
            });
        }
        
        // Close modal if clicked outside
        var modalEl = document.getElementById('mealModal');
        if (modalEl) {
            modalEl.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal();
                }
            });
        }
        
        // Handle Enter key in meal description field
        var mealInput = document.getElementById('mealDescription');
        if (mealInput) {
            mealInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    saveMeal();
                }
            });
        }
    }

    // Call the function to register handlers
    registerEventHandlers();

    function closeModal() {
        document.getElementById('mealModal').style.display = 'none';
        document.getElementById('mealDescription').value = '';
        document.getElementById('mealType').value = 'other';
        currentMealId = null;
        isEditing = false;
    }
      function saveMeal() {
    var mealDescriptionEl = document.getElementById('mealDescription');
    var mealTypeEl = document.getElementById('mealType');
    var saveButton = document.getElementById('saveMeal');
    
    if (!mealDescriptionEl || !mealTypeEl) {
        console.error("Required form elements not found");
        return;
    }
    
    const mealText = mealDescriptionEl.value.trim();
    const mealType = mealTypeEl.value;
    const originalText = saveButton ? saveButton.textContent : "Save Meal";
    
    if (!mealText) {
        // Highlight the input field if empty
        mealDescriptionEl.style.borderColor = '#dc3545';
        setTimeout(() => {
            mealDescriptionEl.style.borderColor = '#ced4da';
        }, 2000);
        return;
    }
    
    if (isEditing && currentMealId) {
        // Update existing meal
        fetch(`/update_meal/${currentMealId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: dateSelected,
                meal: mealText,
                meal_type: mealType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Find and remove the old event
                const existingEvent = calendar.getEventById(currentMealId);
                if (existingEvent) {
                    existingEvent.remove();
                }
                
                // Add the updated event
                calendar.addEvent({
                    id: currentMealId,
                    title: mealText,
                    start: dateSelected,
                    extendedProps: {
                        meal_type: mealType
                    }
                });                        // Refresh calendar event handlers
                    setTimeout(() => {
                        calendar.refetchEvents();
                        console.log("Calendar events refreshed after update");
                        closeModal();
                        var saveButton = document.getElementById('saveMeal');
                        if (saveButton) {
                            saveButton.textContent = originalText;
                            saveButton.style.backgroundColor = '';
                        }
                    }, 1000);
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to update meal. Please try again.');
        });
    } else {
        // Add new meal
        fetch('/add_meal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: dateSelected,
                meal: mealText,
                meal_type: mealType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add the new event to the calendar
                calendar.addEvent({
                    id: data.meal_id,
                    title: mealText,
                    start: dateSelected,
                    extendedProps: {
                        meal_type: mealType
                    }
                });                        // Refresh calendar event handlers
                    setTimeout(() => {
                        calendar.refetchEvents();
                        console.log("Calendar events refreshed after adding new meal");
                        closeModal();
                        var saveButton = document.getElementById('saveMeal');
                        if (saveButton) {
                            saveButton.textContent = originalText;
                            saveButton.style.backgroundColor = '';
                        }
                    }, 1000);
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save meal. Please try again.');
        });
    }
}

    function deleteMeal() {
        if (!currentMealId) return;
        
        fetch(`/delete_meal/${currentMealId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the event from calendar
                const existingEvent = calendar.getEventById(currentMealId);
                if (existingEvent) {
                    existingEvent.remove();
                }
                
                // Close modal
                closeModal();
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete meal. Please try again.');
        });
    }
    
    // Helper function to format date nicely
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }
});