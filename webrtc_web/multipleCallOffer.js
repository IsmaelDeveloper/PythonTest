let saveButtonCounter = 0;
let selectedUsers = [];

function attachSaveButtonEvent(saveButton, userName) {
  saveButton.dataset.isSelected = "false";

  saveButton.addEventListener("click", function () {
    const isSelected = this.dataset.isSelected === "true";
    this.dataset.isSelected = String(!isSelected);

    if (!isSelected) {
      this.style.backgroundColor = "red";
      selectedUsers.push(userName);
      saveButtonCounter += 1;
    } else {
      this.style.backgroundColor = "";
      const index = selectedUsers.indexOf(userName);
      if (index > -1) {
        selectedUsers.splice(index, 1);
      }
      saveButtonCounter -= 1;
    }

    const counterDisplay = document.getElementById("counter-display");
    counterDisplay.innerText = saveButtonCounter + " 개";
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("all-call-button")
    .addEventListener("click", function () {
      console.log(selectedUsers);
    });
});
