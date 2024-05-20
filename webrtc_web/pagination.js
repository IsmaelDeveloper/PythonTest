document.addEventListener("DOMContentLoaded", function () {
  let currentIndex = 0;
  const usersPerPage = 4;
  let allUsers = document.querySelectorAll(".user-container");
  let totalUsers = allUsers.length;
  const prevUsersBtn = document.getElementById("prevUsers");
  const nextUsersBtn = document.getElementById("nextUsers");
  const pageButtonsContainer = document.getElementById("page-buttons");

  function updateUsersVisibility() {
    allUsers.forEach((user, index) => {
      user.style.display =
        index >= currentIndex && index < currentIndex + usersPerPage
          ? "flex"
          : "none";
    });

    prevUsersBtn.disabled = currentIndex === 0;
    nextUsersBtn.disabled = currentIndex + usersPerPage >= totalUsers;

    generatePageButtons();
  }

  prevUsersBtn.onclick = function () {
    currentIndex -= usersPerPage;
    if (currentIndex < 0) currentIndex = 0;
    updateUsersVisibility();
  };

  nextUsersBtn.onclick = function () {
    currentIndex += usersPerPage;
    if (currentIndex > totalUsers - 1) currentIndex = totalUsers - 1;
    updateUsersVisibility();
  };

  function initializePagination() {
    allUsers = document.querySelectorAll(".user-container");
    totalUsers = allUsers.length;
    currentIndex = 0; // Reset to the first page on initialization
    updateUsersVisibility();
  }

  function generatePageButtons() {
    pageButtonsContainer.innerHTML = ""; // Clear previous buttons
    const totalPages = Math.ceil(totalUsers / usersPerPage);

    for (let i = 0; i < totalPages; i++) {
      const pageButton = document.createElement("button");
      pageButton.textContent = i + 1;
      pageButton.classList.add("page-button");
      pageButton.disabled = i === Math.floor(currentIndex / usersPerPage);
      pageButton.onclick = function () {
        currentIndex = i * usersPerPage;
        updateUsersVisibility();
      };
      pageButtonsContainer.appendChild(pageButton);
    }
  }

  window.initializePagination = initializePagination;

  updateUsersVisibility();
});
