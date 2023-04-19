// Function to handle the click event
function handleClick(event) {
    // Get the parent "question-responses" div
    const questionResponsesDiv = event.target.closest('.question-responses');

    // Remove the classes "correct-quiz-selected" and "incorrect-quiz-selected" from all the "correct" and "incorrect" elements in the "question-responses" group
    const allOptions = questionResponsesDiv.querySelectorAll('.correct, .incorrect');
    for (const option of allOptions) {
        option.classList.remove('correct-quiz-selected', 'incorrect-quiz-selected');
    }

    // Add the class "correct-quiz-selected" or "incorrect-quiz-selected" to the clicked element
    if (event.target.classList.contains('correct')) {
        let quizCounterVal = parseInt(document.querySelector("#counter").getAttribute("data-curr"));
        event.target.classList.add('correct-quiz-selected');
        setQuizCounterValue(quizCounterVal+1);
    } else if (event.target.classList.contains('incorrect')) {
        event.target.classList.add('incorrect-quiz-selected');
    }

    for (const option of allOptions) {
        option.removeEventListener('click', handleClick);
    }
}

function setQuizCounterValue(value) {

    let quizCounter = document.querySelector("#counter");
    let maxval = parseInt(quizCounter.getAttribute("data-maximum"));
    quizCounter.setAttribute("data-curr", String(value));
    quizCounter.textContent = String(value) + "/" + String(maxval);
}

function resetQuizSelections() {
    // Select all the "correct" and "incorrect" elements with the "correct-quiz-selected" or "incorrect-quiz-selected" classes
    const selectedOptions = document.querySelectorAll('.correct.correct-quiz-selected, .incorrect.incorrect-quiz-selected');

    // Remove the "correct-quiz-selected" and "incorrect-quiz-selected" classes from the selected elements
    for (const option of selectedOptions) {
        option.classList.remove('correct-quiz-selected', 'incorrect-quiz-selected');
    }
}

document.addEventListener("DOMContentLoaded", function () {

    
    const allCorrectAndIncorrectElements = document.querySelectorAll('.correct, .incorrect');

    const attachClicks = () => {
        for (const element of allCorrectAndIncorrectElements) {
            element.addEventListener('click', handleClick);
        }
    }

    const resetQuiz = () => {
        setQuizCounterValue(0);
        resetQuizSelections();
        attachClicks();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    attachClicks();

    for (let reset_elem of document.querySelectorAll('.reset')) {
        reset_elem.addEventListener('click', resetQuiz);
    }
});
