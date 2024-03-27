document.addEventListener("DOMContentLoaded", function () {
  let currentIndex = 0;
  const usersPerPage = 5;
  let allUsers = document.querySelectorAll(".user-container");
  let totalUsers = allUsers.length;
  const prevUsersBtn = document.getElementById("prevUsers");
  const nextUsersBtn = document.getElementById("nextUsers");
  function updateUsersVisibility() {
    allUsers.forEach((user, index) => {
      user.style.display =
        index >= currentIndex && index < currentIndex + usersPerPage
          ? "flex"
          : "none";
    });

    prevUsersBtn.disabled = currentIndex === 0;
    nextUsersBtn.disabled = currentIndex + usersPerPage >= totalUsers;
  }

  prevUsersBtn.onclick = function () {
    currentIndex -= usersPerPage;
    if (currentIndex < 0) currentIndex = 0;
    updateUsersVisibility();
  };

  nextUsersBtn.onclick = function () {
    currentIndex += usersPerPage;
    if (currentIndex > totalUsers - usersPerPage)
      currentIndex = totalUsers - usersPerPage;
    updateUsersVisibility();
  };

  function initializePagination() {
    allUsers = document.querySelectorAll(".user-container");
    totalUsers = allUsers.length;
    updateUsersVisibility();
  }

  window.initializePagination = initializePagination;

  updateUsersVisibility();
});
