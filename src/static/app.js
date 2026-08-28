document.addEventListener("DOMContentLoaded", () => {
  const capabilitiesList = document.getElementById("capabilities-list");
  const capabilitySelect = document.getElementById("capability");
  const registerForm = document.getElementById("register-form");
  const messageDiv = document.getElementById("message");
  const authButton = document.getElementById("auth-button");
  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("login-form");
  const cancelLoginButton = document.getElementById("cancel-login");
  const registerNote = document.getElementById("register-note");

  let authToken = localStorage.getItem("practiceLeadToken");
  let currentUser = null;

  function getAuthHeaders() {
    return authToken ? { Authorization: `Bearer ${authToken}` } : {};
  }

  function showMessage(message, type = "info") {
    messageDiv.textContent = message;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  function setRegistrationAccess(isEnabled) {
    registerForm.querySelectorAll("input, select, button").forEach((element) => {
      element.disabled = !isEnabled;
    });

    registerNote.textContent = isEnabled
      ? "You are authenticated as a practice lead."
      : "Practice lead access is required to register or unregister consultants.";
  }

  function setLoggedOutState() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem("practiceLeadToken");
    authButton.textContent = "Practice Lead Login";
    setRegistrationAccess(false);
  }

  function setLoggedInState(token, user) {
    authToken = token;
    currentUser = user;
    localStorage.setItem("practiceLeadToken", token);
    authButton.textContent = `Log out ${user.username}`;
    setRegistrationAccess(user.role === "practice_lead");
  }

  async function restoreSession() {
    if (!authToken) {
      setLoggedOutState();
      return;
    }

    try {
      const response = await fetch("/auth/me", {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        setLoggedOutState();
        return;
      }

      const payload = await response.json();
      setLoggedInState(authToken, payload.user);
    } catch (error) {
      setLoggedOutState();
      console.error("Error restoring session:", error);
    }
  }

  function openLoginModal() {
    loginModal.classList.remove("hidden");
  }

  function closeLoginModal() {
    loginModal.classList.add("hidden");
    loginForm.reset();
  }

  // Function to fetch capabilities from API
  async function fetchCapabilities() {
    try {
      const response = await fetch("/capabilities");
      const capabilities = await response.json();

      // Clear loading message
      capabilitiesList.innerHTML = "";
      capabilitySelect.innerHTML = "<option value=\"\">-- Select a capability --</option>";

      // Populate capabilities list
      Object.entries(capabilities).forEach(([name, details]) => {
        const capabilityCard = document.createElement("div");
        capabilityCard.className = "capability-card";

        const availableCapacity = details.capacity || 0;
        const currentConsultants = details.consultants ? details.consultants.length : 0;

        // Create consultants HTML with delete icons
        const consultantsHTML =
          details.consultants && details.consultants.length > 0
            ? `<div class="consultants-section">
              <h5>Registered Consultants:</h5>
              <ul class="consultants-list">
                ${details.consultants
                  .map(
                    (email) => {
                      const deleteButton =
                        currentUser && currentUser.role === "practice_lead"
                          ? `<button class="delete-btn" data-capability="${name}" data-email="${email}">Unregister</button>`
                          : "";

                      return `<li><span class="consultant-email">${email}</span>${deleteButton}</li>`;
                    }
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No consultants registered yet</em></p>`;

        capabilityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Practice Area:</strong> ${details.practice_area}</p>
          <p><strong>Industry Verticals:</strong> ${details.industry_verticals ? details.industry_verticals.join(', ') : 'Not specified'}</p>
          <p><strong>Capacity:</strong> ${availableCapacity} hours/week available</p>
          <p><strong>Current Team:</strong> ${currentConsultants} consultants</p>
          <div class="consultants-container">
            ${consultantsHTML}
          </div>
        `;

        capabilitiesList.appendChild(capabilityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        capabilitySelect.appendChild(option);
      });

      if (currentUser && currentUser.role === "practice_lead") {
        document.querySelectorAll(".delete-btn").forEach((button) => {
          button.addEventListener("click", handleUnregister);
        });
      }
    } catch (error) {
      capabilitiesList.innerHTML =
        "<p>Failed to load capabilities. Please try again later.</p>";
      console.error("Error fetching capabilities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const capability = button.getAttribute("data-capability");
    const email = button.getAttribute("data-email");

    if (!authToken) {
      showMessage("Please log in as a practice lead to unregister consultants.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/capabilities/${encodeURIComponent(
          capability
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");

        // Refresh capabilities list to show updated consultants
        fetchCapabilities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const capability = document.getElementById("capability").value;

    if (!authToken) {
      showMessage("Please log in as a practice lead to register consultants.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/capabilities/${encodeURIComponent(
          capability
        )}/register?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        registerForm.reset();

        // Refresh capabilities list to show updated consultants
        fetchCapabilities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to register. Please try again.", "error");
      console.error("Error registering:", error);
    }
  });

  authButton.addEventListener("click", async () => {
    if (!currentUser) {
      openLoginModal();
      return;
    }

    try {
      await fetch("/auth/logout", {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (error) {
      console.error("Error logging out:", error);
    }

    setLoggedOutState();
    fetchCapabilities();
    showMessage("Logged out successfully.", "info");
  });

  cancelLoginButton.addEventListener("click", closeLoginModal);

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Login failed.", "error");
        return;
      }

      setLoggedInState(result.token, result.user);
      closeLoginModal();
      fetchCapabilities();
      showMessage(`Logged in as ${result.user.username}.`, "success");
    } catch (error) {
      showMessage("Unable to log in. Please try again.", "error");
      console.error("Error logging in:", error);
    }
  });

  // Initialize app
  restoreSession().then(fetchCapabilities);
});
