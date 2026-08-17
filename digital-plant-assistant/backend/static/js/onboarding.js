const steps = [
  {
    question: "How many plants do you currently own?",
    options: ["0", "1-5", "6-15", "15+"]
  },
  {
    question: "Where do you mostly grow your plants?",
    options: ["Indoor", "Balcony", "Garden", "Farm"]
  },
  {
    question: "How experienced are you with plant care?",
    options: ["Beginner", "Intermediate", "Advanced"]
  },
  {
    question: "What is your local climate like?",
    options: ["Tropical", "Dry / Arid", "Temperate", "Cold"]
  }
];

let current = 0;
const answers = {};

const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const progressEl = document.getElementById("progress");
const stepTextEl = document.getElementById("stepText");

function renderStep() {
  const step = steps[current];
  questionEl.textContent = step.question;
  optionsEl.innerHTML = "";

  step.options.forEach(option => {
    const div = document.createElement("div");
    div.className = "option-card";
    div.textContent = option;
    div.onclick = () => {
      answers[current] = option;
      nextStep();
    };
    optionsEl.appendChild(div);
  });

  progressEl.style.width = ((current / steps.length) * 100) + "%";
  stepTextEl.textContent = `Step ${current + 1} of ${steps.length}`;
}

function nextStep() {
  current++;

  if (current < steps.length) {
    renderStep();
  } else {
    // Send answers to backend to compute and save level
    fetch("/api/user/onboard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers: answers })
    }).then(res => res.json())
      .then(data => {
        if (data.success) {
          const user = JSON.parse(localStorage.getItem("user")) || {};
          user.level = data.level;
          localStorage.setItem("user", JSON.stringify(user));
          localStorage.setItem("isNewUser", "false");
          window.location.href = "/dashboard";
        } else {
          alert(data.error || "Failed to save onboarding data.");
          window.location.href = "/dashboard";
        }
      }).catch(err => {
        console.error(err);
        window.location.href = "/dashboard";
      });
  }
}

renderStep();
