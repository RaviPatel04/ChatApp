console.log("✅ chat.js is loaded successfully!");


// ✅ Global Variables (Declared at the top, before any function)
var currentFriendId = null;
var currentFriendName = "";
var currentFriendAvatar = "";
var messagesContainer = null;
let pollingInterval = null;


var currentGroupId = null;
var currentGroupName = "";
var currentGroupAvatar = "";
// var messagesContainer = null;
// let pollingInterval = null;



function toggleProfile() {
    const popup = document.getElementById('profilePopup');
    popup.classList.toggle('invisible');
    document.body.classList.toggle('overflow-hidden');
}

function previewAvatar(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('avatarPreview').src = e.target.result;
        }
        reader.readAsDataURL(file);
    }
}


// Handle form submission
document.getElementById('profileForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });

        // ✅ Check if response is JSON before parsing
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error("❌ Server returned an invalid response (HTML instead of JSON).");
        }

        const data = await response.json();

        if (data.success) {
            alert("✅ " + data.message);

            // ✅ Check if the avatar element exists before updating
            const avatarInput = document.getElementById('avatarInput');
            const profileImage = document.querySelector('.profile-button img');

            if (avatarInput.files.length > 0 && profileImage) {
                profileImage.src = URL.createObjectURL(avatarInput.files[0]);
            }

            toggleProfile(); // ✅ Close popup after successful update
        } else {
            alert("❌ " + data.message);
        }
    } catch (error) {
        alert("❌ Error updating profile. Check console for details.");
        console.error("❌ Network/Server error:", error);
    }
});






function loadMessages(friendId, friendName, friendAvatar) {
    console.log("🔹 Loading messages for friend ID:", friendId, friendName);
    // ✅ Clear active state for both friends & groups
    document.querySelectorAll(".friend-item, .group-item").forEach(item => {
        item.classList.remove("bg-gray-50");
    });

    currentFriendId = friendId;
    currentFriendName = friendName;
    currentFriendAvatar = friendAvatar;

    let chatWindow = document.getElementById("chatWindow");
    let welcomeMessage = document.getElementById("welcomeMessage");

    // ✅ Hide Welcome Message & Show Chat
    if (welcomeMessage) welcomeMessage.classList.add("invisible", "opacity-0");
    chatWindow.classList.remove("invisible", "opacity-0");
    chatWindow.classList.add("opacity-100");

    document.getElementById("chatUsername").textContent = friendName;
    document.getElementById("chatAvatar").src = friendAvatar;

    messagesContainer = document.getElementById("messagesContainer");
    messagesContainer.innerHTML = ""; // ✅ Clear old messages

    fetchMessages(); // ✅ Load messages

    // ✅ Remove highlight from all friends
    document.querySelectorAll(".friend-item").forEach(friend => {
        friend.classList.remove("bg-gray-50"); // ✅ Remove highlight
    });

    // ✅ Add highlight to the selected friend
    let selectedFriend = document.querySelector(`.friend-item[data-friend-id="${friendId}"]`);
    if (selectedFriend) {
        selectedFriend.classList.add("bg-gray-50"); // ✅ Highlight with blue background
    }

    // ✅ Ensure "Enter Key" Event Listener is Attached
    setTimeout(() => {  // ✅ Wait for input field to load
        let messageInput = document.getElementById("messageInput");
        if (messageInput) {
            messageInput.removeEventListener("keypress", handleEnterKey);
            messageInput.addEventListener("keypress", handleEnterKey);
        } else {
            console.error("❌ Error: #messageInput not found!");
        }
    }, 200);  // ✅ Ensures input field is available before attaching event

    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(fetchMessages, 3000);
}


function handleEnterKey(event) {
    let messageInput = event.target;

    if (event.key === "Enter") {
        if (event.shiftKey) {
            // ✅ Prevents message sending
            messageInput.style.height = "auto";  // ✅ Reset height for recalculation
            messageInput.style.height = Math.min(messageInput.scrollHeight, 96) + "px"; // ✅ Max height = 96px (h-24)
            return;
        }
        event.preventDefault();  // ✅ Prevents default Enter behavior (form submission)
        selected();
        // sendGroupMessage();
        messageInput.style.height = "auto";  // ✅ Reset height after sending (h-12)
    }
}





// ✅ Function to Fetch New Messages
function fetchMessages() {
    if (!currentFriendId) return;

    let messagesContainer = document.getElementById("messagesContainer");

    // ✅ Check if user is at the bottom before fetching messages
    let isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 10;

    fetch(`/get-messages/${currentFriendId}/`)
        .then(response => response.json())
        .then(data => {

            if (!data.messages || data.messages.length === 0) {
                messagesContainer.innerHTML = "<p class='text-center text-gray-500 mt-10'>No messages yet. Start the conversation!</p>"; // ✅ Show empty message
                return;
            }

            let lastMessageId = messagesContainer.lastElementChild ? messagesContainer.lastElementChild.dataset.messageId : null;

            data.messages.forEach(msg => {
                if (document.querySelector(`[data-message-id = "${msg.id}"]`)) return; // ✅ Prevent duplicates
                displayMessage(msg, currentFriendAvatar);
                
            });

            // ✅ Auto-scroll ONLY if the user was already at the bottom
            if (isAtBottom) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        })
        .catch(error => console.error("❌ Error fetching messages:", error));
}




// ✅ Function to Send Messages
function sendMessage() {

    if (!currentFriendId) {
        console.error("Error: No friend selected!");
        return;
    }
    console.log("Sending group message to Group ID:", currentFriendId);

    let messageInput = document.getElementById("messageInput");
    let messageText = messageInput.value.trim();

    if (!messageText || !currentFriendId) {
        console.error("Error: Message or Friend ID missing!");
        return;
    }

    fetch("/send-message/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        
        body: `receiver_id=${currentFriendId}&text=${encodeURIComponent(messageText)}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messageInput.value = "";  // ✅ Clear Input Field
                displayMessage(data.message, ""); // ✅ Show Sent Message Instantly

                // ✅ Force auto-scroll when User 1 sends a message
                let messagesContainer = document.getElementById("messagesContainer");
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else {
                console.error("Error sending message:", data.error);
            }
        })
        .catch(error => console.error("Network error while sending message:", error));
}




function closeChat() {
    let chatWindow = document.getElementById("chatWindow");
    let welcomeMessage = document.getElementById("welcomeMessage");

    // ✅ Hide Chat Window
    chatWindow.classList.add("opacity-0");
    setTimeout(() => {
        chatWindow.classList.add("invisible");
        if (welcomeMessage) {
            welcomeMessage.classList.remove("invisible", "opacity-0");
            welcomeMessage.classList.add("opacity-100");
        }
    }, 300); // Matches `transition-opacity duration-300`

    setTimeout(() => {
        // ✅ Remove highlight from all friends
        document.querySelectorAll(".friend-item").forEach(friend => {
            friend.classList.remove("bg-gray-50"); // ✅ Remove highlight
        });
    }, 500); 


    // ✅ Stop polling for new messages
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }

    console.log("🔹 Chat closed. Showing welcome message.");
}



function openProfilePopup() {
    // if (!currentFriendId) return; // ✅ Don't open if no friend is selected

    console.log("currentFriendId: ",currentFriendId);
    console.log("currentGroupId: ",currentGroupId);


    if (currentFriendId) {
        fetch(`/get-user-profile/${currentFriendId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("popupAvatar").src = data.avatar;
            document.getElementById("popupUsername").textContent = data.username;
            document.getElementById("popupEmail").textContent = data.email;
            document.getElementById("popupBio").textContent = data.bio || "No bio available.";

            let popup = document.getElementById("profilePopupFriend");
            popup.classList.remove("invisible", "opacity-0");
            popup.classList.add("opacity-100");
        })
        .catch(error => console.error("❌ Error fetching profile:", error));
    }

    if (currentGroupId) {
        console.log(currentGroupId);
        // Function to fetch group profile based on groupId
        
        fetch(`/get-group-profile/${currentGroupId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("popupGroupAvatar").src = data.group_avatar;
            document.getElementById("popupGroupName").textContent = data.group_name;
            document.getElementById("popupAdmin").textContent = data.group_admin;
            document.getElementById("popupGroupBio").textContent = data.group_bio || "No bio available.";


            document.getElementById("popupGroupNameEdit").value = data.group_name;
            document.getElementById("popupGroupBioEdit").value = data.group_bio || "";
            // document.getElementById("popupGroupAvatarEdit").value = data.group_avatar;



            // Check if the current user is the admin
            const isAdmin = data.is_admin;

            if (isAdmin) {
                // Show editable fields for admin
                document.getElementById("popupGroupName").classList.add("hidden");
                document.getElementById("popupGroupNameEdit").classList.remove("hidden");

                document.getElementById("popupGroupBio").classList.add("hidden");
                document.getElementById("popupGroupBioEdit").classList.remove("hidden");

                document.getElementById("popupGroupAvatarEdit").classList.remove("invisible");

                document.getElementById("saveGroupProfile").classList.remove("hidden");
            }else{
                // Show only read-only fields for non-admins
                document.getElementById("popupGroupName").classList.remove("hidden");
                document.getElementById("popupGroupNameEdit").classList.add("hidden");

                document.getElementById("popupGroupBio").classList.remove("hidden");
                document.getElementById("popupGroupBioEdit").classList.add("hidden");

                document.getElementById("saveGroupProfile").classList.add("hidden");
            }
            // Show the profile popup
            let popup = document.getElementById("profilePopupGroup");
            popup.classList.remove("invisible", "opacity-0");
            popup.classList.add("opacity-100");

        })
        .catch(error => console.error("❌ Error fetching group profile:", error));   
    }
}
// Preview avatar before uploading
function previewGroupAvatar(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById("popupGroupAvatar").src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

// Save updated group profile
function saveGroupProfile() {
    const newGroupName = document.getElementById("popupGroupNameEdit").value;
    const newGroupBio = document.getElementById("popupGroupBioEdit").value;
    const avatarFile = document.getElementById("groupAvatarInput").files[0];

    let formData = new FormData();
    formData.append("group_name", newGroupName);
    formData.append("group_bio", newGroupBio);
    if (avatarFile) {
        formData.append("group_avatar", avatarFile);
    }

    fetch(`/update-group-profile/${currentGroupId}/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Group profile updated successfully!");
            window.location.reload();
            // openProfilePopup();
        } else {
            alert("Error updating group profile.");
        }
    })
    .catch(error => console.error("❌ Error saving group profile:", error));
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function closeProfilePopup() {

    if (currentFriendId) {
        let popup = document.getElementById("profilePopupFriend");
        popup.classList.add("opacity-0"); 
        setTimeout(() => {
            popup.classList.add("invisible"); // ✅ Hide completely after animation
        }, 300); // Matches `transition-opacity duration-300`
    }

    if (currentGroupId) {
        let grouppopup = document.getElementById("profilePopupGroup");
        grouppopup.classList.add("opacity-0"); 
        setTimeout(() => {
            grouppopup.classList.add("invisible"); // ✅ Hide completely after animation
        }, 300); 
    }
    
    
}




// ✅ Open Voice Recorder Popup & Start Recording
// ✅ Start Recording Function
document.addEventListener("DOMContentLoaded", () => {
    let mediaRecorder;
    let audioChunks = [];
    let recordedAudioBlob = null;

    function openVoicePopup() {
        let voicePopup = document.getElementById("voiceRecorderPopup");
        voicePopup.classList.remove("invisible", "opacity-0");
        voicePopup.classList.add("opacity-100");

        // ✅ Reset recording state when opening popup again
        resetRecordingUI();
    }

    function closeVoicePopup() {
        let voicePopup = document.getElementById("voiceRecorderPopup");
        voicePopup.classList.add("opacity-0");
        setTimeout(() => {
            voicePopup.classList.add("invisible");
        }, 300);

        // ✅ Reset everything when closing
        resetRecordingUI();
    }

    function resetRecordingUI() {
        document.getElementById("recordingStatus").textContent = "🎤 Press to start recording";
        document.getElementById("startRecordingButton").classList.remove("hidden");
        document.getElementById("stopRecordingButton").classList.add("hidden");
        document.getElementById("sendRecordingButton").classList.add("hidden");
        document.getElementById("audioPlayback").classList.add("hidden");
        document.getElementById("audioPlayback").src = ""; // ✅ Clear previous audio
        recordedAudioBlob = null; // ✅ Reset audio data
    }

    function startRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    recordedAudioBlob = new Blob(audioChunks, { type: "audio/webm" });
                    let audioURL = URL.createObjectURL(recordedAudioBlob);
                    document.getElementById("audioPlayback").src = audioURL;
                    document.getElementById("audioPlayback").classList.remove("hidden");
                    document.getElementById("sendRecordingButton").classList.remove("hidden");
                };

                mediaRecorder.start();
                document.getElementById("recordingStatus").textContent = "🎤 Recording...";
                document.getElementById("startRecordingButton").classList.add("hidden");
                document.getElementById("stopRecordingButton").classList.remove("hidden");

                // ✅ Save stream reference to stop it properly
                mediaRecorder.stream = stream;
            })
            .catch(error => console.error("❌ Microphone access denied:", error));
    }

    document.getElementById("startRecordingButton").addEventListener("click", function () {
        startRecording();
    });

    document.getElementById("stopRecordingButton").addEventListener("click", function () {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            document.getElementById("recordingStatus").textContent = "✅ Recording stopped!";
            document.getElementById("stopRecordingButton").classList.add("hidden");

            // ✅ Properly stop the microphone after recording
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    });

    document.getElementById("sendRecordingButton").addEventListener("click", function () {
        if (!recordedAudioBlob || (!currentFriendId && !currentGroupId)) {
            console.error("No recording available or no friend selected!");
            return;
        }

        let formData = new FormData();
        formData.append("voice_message", recordedAudioBlob);
        // formData.append("receiver_id", currentFriendId);
        
        if (currentGroupId) {
            formData.append("group_id", currentGroupId);
            sendVoiceMessage(formData, "/send-voice-message/");
        } else if (currentFriendId) {
            formData.append("receiver_id", currentFriendId);
            sendVoiceMessage(formData, "/send-voice-message/");
        }

        // fetch("/send-voice-message/", {
        //     method: "POST",
        //     body: formData,
        //     headers: {
        //         "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        //     }
        // })
        //     .then(response => response.json())
        //     .then(data => {
        //         if (data.success) {
        //             console.log("✅ Voice message sent!");

        //             // ✅ Show the sent voice message immediately
        //             // displayVoiceMessage(data.message);

        //             closeVoicePopup();

        //             // ✅ Reset UI elements
        //             // ✅ Reset recording UI but keep popup open
        //             resetRecordingUI();

        //             // ✅ Allow new recording
        //             // document.getElementById("startRecordingButton").classList.remove("hidden");
        //         } else {
        //             console.error("❌ Error sending voice message:", data.error);
        //         }
        //     });
    });

    // ✅ Open Popup when Mic Button is Clicked
    document.getElementById("recordButton").addEventListener("click", () => {
        openVoicePopup();
    });

    // ✅ Close Popup when "X" button is clicked
    document.getElementById("closeVoicePopupButton").addEventListener("click", () => {
        closeVoicePopup();
    });

    
function sendVoiceMessage(formData, url) {
    fetch(url, {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("✅ Voice message sent!");

            // ✅ Show the sent voice message immediately
            if (currentGroupId) {
                displayGroupMessage(data.message);
            } else {
                displayMessage(data.message);
            }

            closeVoicePopup();
            // ✅ Reset recording UI
            resetRecordingUI();
        } else {
            console.error("❌ Error sending voice message:", data.error);
        }
    })
    .catch(error => console.error("❌ Network error:", error));
}
});




document.getElementById("attachmentInput").addEventListener("change", function (event) {
    let file = event.target.files[0];
    if (!file) return;

    let formData = new FormData();
    formData.append("attachment", file);

    // Check if sending to a group or an individual
    if (currentGroupId) {
        formData.append("group_id", currentGroupId);
    } else {
        formData.append("receiver_id", currentFriendId);
    }
    // formData.append("receiver_id", currentFriendId);

    fetch("/send-attachment/", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("✅ File sent successfully!");
            displayMessage(data.message, currentFriendAvatar);
        } else {
            console.error("Error sending file:", data.error);
        }
    })
    .catch(error => console.error("Network error while sending file:", error));
    
    event.target.value = "";

});




// Friend Request JavaScript - Fixed Version
let notificationsOpen = false;
let unreadNotifications = 0;

// ✅ Open and Close Friend Request Popup
function openAddFriendPopup() {
    document.getElementById("addFriendPopup").classList.remove("hidden");
    document.getElementById("addFriendPopup").classList.add("flex");
}

function closeAddFriendPopup() {
    document.getElementById("addFriendPopup").classList.add("hidden");
    document.getElementById("addFriendPopup").classList.remove("flex");
    // Clear inputs
    document.getElementById("friendUsername").value = "";
    document.getElementById("friendEmail").value = "";
}

// Send friend request
function sendFriendRequest() {
    const username = document.getElementById("friendUsername").value.trim();
    const email = document.getElementById("friendEmail").value.trim();
    
    if (!username || !email) {
        showAlert("Please enter both username and email", "error");
        return;
    }
    
    fetch('/send-friend-request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert(data.message, "success");
            closeAddFriendPopup();
        } else {
            showAlert(data.message, "error");
        }
    })
    .catch(error => {
        showAlert("An error occurred. Please try again.", "error");
        console.error('Error:', error);
    });
}

// Show notification popup
function toggleNotifications() {
    const notificationPopup = document.getElementById("notificationPopup");
    
    if (notificationsOpen) {
        notificationPopup.classList.add("invisible", "opacity-100");
        notificationsOpen = false;
    } else {
        loadNotifications();
        notificationPopup.classList.remove("invisible", "opacity-0");
        notificationsOpen = true;
    }
}

// Load notifications from server
function loadNotifications() {
    fetch('/notifications/')
    .then(response => response.json())
    .then(data => {
        const notificationList = document.getElementById("notificationList");
        notificationList.innerHTML = '';
        
        if (data.notifications.length === 0) {
            notificationList.innerHTML = '<div class="p-4 text-gray-500">No notifications</div>';
            return;
        }
        
        data.notifications.forEach(notification => {
            const notificationItem = document.createElement('div');
            notificationItem.className = `p-3 border-b border-gray-400 ${notification.read ? 'bg-white' : 'bg-blue-50'}`;
            notificationItem.id = `notification-${notification.id}`;
            
            let actionButtons = '';
            let message = '';
            
            if (notification.type === 'friend_request') {
                message = `<b>${notification.sender_username}</b> sent you a friend request`;
                actionButtons = `
                    <div class="mt-2 flex space-x-4">
                        <button onclick="handleFriendRequest(${notification.request_id}, 'accept', ${notification.id})" 
                                class="px-4 py-1 bg-green-500 text-white rounded-lg hover:bg-green-600 mr-2">
                            Accept
                        </button>
                        <button onclick="handleFriendRequest(${notification.request_id}, 'reject', ${notification.id})" 
                                class="px-4 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600">
                            Reject
                        </button>
                    </div>
                `;
            } else if (notification.type === 'group_invite') {
                console.log("notification: ",notification)
                console.log("group_name: ",notification.group_name)
                console.log("group_request_id: ",notification.group_request_id)
                message = `<b>${notification.sender_username}</b> invited you to join group<b>${notification.group_name}</b>`;
                actionButtons = `
                    <div class="mt-2 flex space-x-4">
                        <button onclick="handleGroupRequest(${notification.group_request_id}, 'accept', ${notification.id})" 
                                class="px-4 py-1 bg-green-500 text-white rounded-lg hover:bg-green-600 mr-2">
                            Accept
                        </button>
                        <button onclick="handleGroupRequest(${notification.group_request_id}, 'reject', ${notification.id})" 
                                class="px-4 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600">
                            Reject
                        </button>
                    </div>
                `;
            } else if (notification.type === 'group_invite_accepted') {
                console.log("notification: ",notification)
                console.log("group_name: ",notification.group_name)
                message = `<b>${notification.sender_username}</b> accepted your invitation to join group <b>${notification.group_name}</b>`;
            } else if (notification.type === 'group_invite_rejected') {
                message = `<b>${notification.sender_username}</b> rejected your invitation to join group <b>${notification.group_name}</b>`;
            } else if (notification.type === 'request_accepted') {
                message = `<b>${notification.sender_username}</b> accepted your friend request`;
            } else if (notification.type === 'request_rejected') {
                message = `<b>${notification.sender_username}</b> rejected your friend request`;
            }
            
            notificationItem.innerHTML = `
                <div class="flex justify-between">
                    <div>
                        <div>${message}</div>
                        <div class="text-xs text-gray-500">${notification.created_at}</div>
                        ${actionButtons}
                    </div>
                    ${actionButtons ? '' : `
                        <button onclick="dismissNotification(${notification.id})" class="text-blue-500 hover:text-blue-700">
                            <i class="fas fa-check"></i>
                        </button>
                        `}
                </div>
            `;
            
            notificationList.appendChild(notificationItem);
        });
        
        // Update notification badge
        updateNotificationBadge(data.unread_count);
    })
    .catch(error => {
        console.error('Error loading notifications:', error);
    });
}

// Handle friend request (accept/reject) with complete notification removal
function handleFriendRequest(requestId, action, notificationId) {
    fetch('/handle-friend-request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            request_id: requestId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert(data.message, "success");
            
            // Remove the notification from the UI immediately
            removeNotificationFromUI(notificationId);
            
            // Delete the notification completely instead of just marking as read
            fetch(`/notifications/${notificationId}/delete/`, {
                method: 'POST'
            })
            .catch(error => {
                console.error('Error deleting notification:', error);
            });
            window.location.reload(); 
            
            // Reload notifications to update the badge
            setTimeout(function() {
                if (notificationsOpen) {
                    loadNotifications();
                } else {
                    updateNotificationCount();
                }
            }, 500);
        } else {
            showAlert(data.message, "error");
        }
    })
    .catch(error => {
        showAlert("An error occurred. Please try again.", "error");
        console.error('Error:', error);
    });
}

// Dismiss notification (completely remove from database)
function dismissNotification(notificationId) {
    // Remove the notification from the UI first for immediate feedback
    removeNotificationFromUI(notificationId);

    // Delete the notification from the database
    fetch(`/notifications/${notificationId}/delete/`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // Update notification count after successful deletion
        updateNotificationCount();
        window.location.reload();
    })
    .catch(error => {
        console.error('Error deleting notification:', error);
    });
}

// Remove notification from UI
function removeNotificationFromUI(notificationId) {
    const notificationElement = document.getElementById(`notification-${notificationId}`);
    if (notificationElement) {
        notificationElement.remove();
        
        // Check if there are no more notifications
        const notificationList = document.getElementById("notificationList");
        if (notificationList.children.length === 0) {
            notificationList.innerHTML = '<div class="p-4 text-gray-500">No notifications</div>';
        }
    }
}





// ----------------------------------------------------------------------------------------------
// Mark notification as read
function markNotificationAsRead(notificationId) {
    fetch(`/notifications/${notificationId}/mark-read/`, {
        method: 'POST'
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error marking notification as read:', error);
    });
}
// ------------------------------------------------------------------------------------------------------





// Update notification count only
function updateNotificationCount() {
    fetch('/notifications/count/')
    .then(response => response.json())
    .then(data => {
        updateNotificationBadge(data.unread_count);
    })
    .catch(error => {
        console.error('Error updating notification count:', error);
    });
}

// Update notification badge
function updateNotificationBadge(count) {
    const badge = document.getElementById("notificationBadge");
    unreadNotifications = count;
    
    if (count > 0) {
        badge.textContent = count > 9 ? '9+' : count;
        badge.classList.remove("hidden");
    } else {
        badge.classList.add("hidden");
    }
}

// Show alert message
function showAlert(message, type) {
    const alertElement = document.createElement('div');
    alertElement.className = `fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white z-50`;
    alertElement.textContent = message;
    
    document.body.appendChild(alertElement);
    
    setTimeout(() => {
        alertElement.remove();
    }, 3000);
}

// Load notifications count on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get initial notification count
    fetch('/notifications/')
    .then(response => response.json())
    .then(data => {
        updateNotificationBadge(data.unread_count);
    });
    
    // Set up periodic refresh of notifications (every 30 seconds)
    setInterval(() => {
        if (!notificationsOpen) {
            fetch('/notifications/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.unread_count);
                
                // Show alert for new notifications
                if (data.unread_count > unreadNotifications) {
                    showAlert("You have new notifications", "success");
                }
            });
        }
    }, 10000);
});















// 27/03/2025
function openAddGroupPopup() {
    const popup = document.getElementById("addGroupPopup");
    popup.classList.remove("hidden");
    popup.classList.add("flex");
}
  
function closeAddGroupPopup() {
    const popup = document.getElementById("addGroupPopup");
    popup.classList.add("hidden");
    popup.classList.remove("flex");
    document.getElementById("groupNameInput").value = "";
}
  
function createGroup() {
    const groupName = document.getElementById("groupNameInput").value.trim();
    
    if (!groupName) {
      alert("Please enter a group name");
      return;
    }
  
    fetch("/create-group/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
      },
      body: JSON.stringify({ group_name: groupName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
          alert(data.message);
          closeAddGroupPopup();
          // Reload page or dynamically update group list
          window.location.reload(); 
        } else {
          alert("Error: " + data.message);
        }
    })
    .catch(err => console.error("Error creating group:", err));
}
  


function openAddMemberPopup() {
    document.getElementById("addMemberPopup").classList.remove("hidden");
    document.getElementById("addMemberPopup").classList.add("flex");
}
  
function closeAddMemberPopup() {
    document.getElementById("addMemberPopup").classList.add("hidden");
    document.getElementById("addMemberPopup").classList.remove("flex");
    document.getElementById("addMemberUsername").value = "";
    document.getElementById("addMemberEmail").value = "";
}




function sendGroupInvite() {
    const username = document.getElementById("addMemberUsername").value.trim();
    const email = document.getElementById("addMemberEmail").value.trim();
  
    if (!currentGroupId) {
      alert("No group selected!");
      return;
    }
    if (!username || !email) {
      alert("Please fill in username and email.");
      return;
    }
  
    fetch("/send-group-invite/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
      },
      body: JSON.stringify({
        group_id: currentGroupId,
        username: username,
        email: email
      })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
          alert(data.message);
          closeAddMemberPopup();
        } else {
          alert("Error: " + data.message);
        }

    })
    .catch(error => console.error("Error inviting member:", error));
}






function handleGroupRequest(requestId, action, notificationId) {
    console.log("Handling group request:", requestId, action,notificationId);
    fetch("/handle-group-request/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: JSON.stringify({
            request_id: requestId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response from handle_group_request:", data);
        // if (data.success) {
        //     alert(data.message);
        //     // Remove notification from UI
        //     const notifElem = document.getElementById(`notification-${notificationId}`);
        //     if (notifElem) {
        //         notifElem.remove();
        //     }

        //     // Delete the notification completely instead of just marking as read
        //     fetch(`/notifications/${notificationId}/delete/`, {
        //         method: 'POST'
        //     })
        //     .catch(error => {
        //         console.error('Error deleting notification:', error);
        //     });
        if (data.success) {
            showAlert(data.message, "success");
            
            // Remove the notification from the UI immediately
            removeNotificationFromUI(notificationId);
            
            // Delete the notification completely instead of just marking as read
            fetch(`/notifications/${notificationId}/delete/`, {
                method: 'POST'
            })
            .catch(error => {
                console.error('Error deleting notification:', error);
            });
            
            window.location.reload();

            
            // Reload notifications to update the badge
            setTimeout(function() {
                if (notificationsOpen) {
                    loadNotifications();
                } else {
                    updateNotificationCount();
                }
            }, 500);

        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(error => console.error("Error handling group request:", error));
}


























// function loadGroupMessages(groupId, groupName) {
//     console.log("🔹 Loading messages for group:", groupId);

//     currentGroupId = groupId;

//     document.getElementById("chatUsername").textContent = groupName;
//     document.getElementById("messagesContainer").innerHTML = "";

//     fetch(`/get-group-messages/${groupId}/`)
//         .then(response => response.json())
//         .then(data => {
//             data.messages.forEach(msg => {
//                 displayMessage(msg, "");
//             });
//         });
// }
// function sendGroupMessage() {
//     let messageInput = document.getElementById("messageInput");
//     let messageText = messageInput.value.trim();

//     if (!messageText || !currentGroupId) return;

//     fetch("/send-group-message/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ group_id: currentGroupId, text: messageText })
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.success) {
//             messageInput.value = "";
//             displayMessage(data.message, "");
//         }
//     });
// }







//27/03/2025


// Similar to loadMessages but for groups
function loadGroupMessages(groupId, groupName, GroupAvatar) {
    console.log("🔹 Loading group messages for:",groupId, groupName);
    // ✅ Clear active state for both friends & groups
    document.querySelectorAll(".friend-item, .group-item").forEach(item => {
        item.classList.remove("bg-gray-50");
    });

    currentGroupId = groupId;
    currentGroupName = groupName;
    console.log("Current Group ID:", currentGroupId);

    // Hide welcome message, show chat window
    let chatWindow = document.getElementById("chatWindow");
    let welcomeMessage = document.getElementById("welcomeMessage");

    // ✅ Hide Welcome Message & Show Chat
    if (welcomeMessage) welcomeMessage.classList.add("invisible", "opacity-0");
    chatWindow.classList.remove("invisible", "opacity-0");
    chatWindow.classList.add("opacity-100");

    document.getElementById("chatUsername").textContent = groupName;
    // Possibly show group avatar if you implement that
    // document.getElementById("chatAvatar").src = "../media/group_avatars/group_default.png";
    document.getElementById("chatAvatar").src = GroupAvatar;

    messagesContainer = document.getElementById("messagesContainer");
    messagesContainer.innerHTML = "";

    fetchGroupMessages();
    // // fetch messages
    // fetch(`/get-group-messages/${groupId}/`)
    // .then(res => res.json())
    // .then(data => {
    //     if (!data.messages || data.messages.length === 0) {
    //         messagesContainer.innerHTML = "<p class='text-center text-gray-500 mt-10'>No messages yet in this group.</p>";
    //         return;
    //     }
    //     data.messages.forEach(msg => {
    //         displayMessage(msg, ""); // Reuse your existing displayMessage but pass empty avatar or adapt it
    //     });
    //     messagesContainer.scrollTop = messagesContainer.scrollHeight;
    // })
    // .catch(err => console.error("Error loading group messages:", err));


    // ✅ Remove highlight from all friends
    document.querySelectorAll(".group-item").forEach(group => {
        group.classList.remove("bg-gray-50"); // ✅ Remove highlight
    });

    // ✅ Add highlight to the selected friend
    let selectedGroup = document.querySelector(`.group-item[data-group-id="${groupId}"]`);
    if (selectedGroup) {
        selectedGroup.classList.add("bg-gray-50"); // ✅ Highlight with blue background
    }

    // ✅ Ensure "Enter Key" Event Listener is Attached
    setTimeout(() => {  // ✅ Wait for input field to load
        let messageInput = document.getElementById("messageInput");
        if (messageInput) {
            messageInput.removeEventListener("keypress", handleEnterKey);
            messageInput.addEventListener("keypress", handleEnterKey);
        } else {
            console.error("❌ Error: #messageInput not found!");
        }
    }, 200);  // ✅ Ensures input field is available before attaching event    

    // If you want polling, set an interval to re-fetch group messages
    // if (pollingInterval) clearInterval(pollingInterval);
    // pollingInterval = setInterval(() => {
    //     fetchGroupMessages();
    // }, 3000);
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(fetchGroupMessages, 3000);
}



















function fetchGroupMessages() {
    if (!currentGroupId) return;

    let messagesContainer = document.getElementById("messagesContainer");

    let isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 10;

    fetch(`/get-group-messages/${currentGroupId}/`)
        .then(response => response.json())
        .then(data => {

            if (!data.messages || data.messages.length === 0) {
                messagesContainer.innerHTML = "<p class='text-center text-gray-500 mt-10'>No messages yet. Start the conversation!</p>"; // ✅ Show empty message
                return;
            }

            let lastMessageId = messagesContainer.lastElementChild ? messagesContainer.lastElementChild.dataset.messageId : null;

            data.messages.forEach(msg => {
                if (document.querySelector(`[data-message-id = "${msg.id}"]`)) return; // ✅ Prevent duplicates
                // displayMessage(msg, "");
                displayGroupMessage(msg,msg.sender_avatar,msg.sender)
                
            });

            // ✅ Auto-scroll ONLY if the user was already at the bottom
            if (isAtBottom) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }

            // data.messages.forEach(msg => {
            //     // If we haven't already displayed it, display it
            //     if (!document.querySelector(`[data-message-id="${msg.id}"]`)) {
            //     displayMessage(msg, "");
            //     }
            // });
        
        })
        .catch(err => console.error("Error fetching group messages:", err));
}






// Similar to sendMessage but for group
function sendGroupMessage() {
    if (!currentGroupId) {
        console.error("Error: No group selected!");
        return;
    }
    console.log("Sending group message to Group ID:", currentGroupId);

    let messageInput = document.getElementById("messageInput");
    let messageText = messageInput.value.trim();

    if (!messageText || !currentGroupId){ 
        console.error("Error: Message or Group ID missing!");
        return;
    }

    fetch("/send-group-message/", {
        method: "POST",
        headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        // body: `receiver_id=${currentGroupId}&text=${encodeURIComponent(messageText)}`
        body: JSON.stringify({
        group_id: currentGroupId,
        text: messageText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageInput.value = "";
            displayGroupMessage(data.message, "");
            // displayMessage(data.message, "");

            let messagesContainer = document.getElementById("messagesContainer");
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else {
            console.error("Error sending group message:", data.error);
        }
    })
    .catch(err => console.error("Network error:", err));
}



function selected() {

    if (currentGroupId) {
      sendGroupMessage();
    } else if (currentFriendId) {
      sendMessage();
    } else {
      console.error("Error: No group or friend selected!");
    }
}
  











// Switching to Groups
function openGroup(groupId, groupName, GroupAvatar, groupAdminUsername) {
    // Set the current group ID
    currentGroupId = groupId;
    currentFriendId = null; // Clear the friend context
    showAddMemberButton(groupAdminUsername);
    
    

    // Now load group messages
    loadGroupMessages(groupId, groupName, GroupAvatar);
}

// Switching to a Friend in People
function openFriend(friendId, friendName, friendAvatar) {
    // Set the current friend ID
    currentFriendId = friendId;
    currentGroupId = null; // Clear the group context
    
    document.getElementById("addMemberButton").style.display = "none";


    // Load friend messages
    loadMessages(friendId, friendName, friendAvatar);
}




// function openGroupProfilePopup() {
//     if (!currentFriendId) return; // ✅ Don't open if no friend is selected

//     fetch(`/get-user-profile/${currentFriendId}/`)
//         .then(response => response.json())
//         .then(data => {
//             document.getElementById("popupAvatar").src = data.avatar;
//             document.getElementById("popupUsername").textContent = data.username;
//             document.getElementById("popupEmail").textContent = data.email;
//             document.getElementById("popupBio").textContent = data.bio || "No bio available.";

//             let popup = document.getElementById("profilePopupFriend");
//             popup.classList.remove("invisible", "opacity-0");
//             popup.classList.add("opacity-100");
//         })
//         .catch(error => console.error("❌ Error fetching profile:", error));
// }


// function openProfilePopupOrGroup(id, name, avatarUrl, type) {
//     // Conditional logic based on type
//     if (type === 'group') {
//         openGroupProfilePopup(id, name, avatarUrl);  // Open group profile
//     } else if (type === 'friend') {
//         openProfilePopup(id, name, avatarUrl);  // Open friend profile
//     } else {
//         console.error("Invalid type! Must be 'group' or 'friend'.");
//     }
// }


function showAddMemberButton(groupAdminUsername) {
    let isAdmin = document.getElementById("isAdmin")?.textContent.trim();
    let groupAdmin = groupAdminUsername;
    let addMemberButton = document.getElementById("addMemberButton");

    // Compare the usernames instead of Boolean values
    if (isAdmin === groupAdmin) {
        console.log("✅ User is admin, showing button!");
        addMemberButton.style.display = "flex";
    } else {
        console.log("❌ User is NOT admin, hiding button.");
        addMemberButton.style.display = "none";
    }
}



