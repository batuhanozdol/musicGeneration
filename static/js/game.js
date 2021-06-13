const question = document.querySelector('#question');
const choices = Array.from(document.querySelectorAll('.choice-text'));
const progressText = document.querySelector('#progressText');
const scoreText = document.querySelector('#score');
const progressBarFull = document.querySelector('#progressBarFull');

let currentQuestion = {}
let acceptingAnswers = true
let score = 0
let questionCounter = 0
let availableQuestions = []

let questions = [
    {
        question: "<audio controls><source src='static/suha1.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/shorter_lstmbilstmbilstm20.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/shorter_bilstmatt40.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/bilstm_att_lstm_40.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/bilstm_att_BiGru_25_100nota.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/gan_final_epoch1000.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 2,
    },
    {
        question: "<audio controls><source src='static/mozk331b.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 1,
    },
    {
        question: "<audio controls><source src='static/mozk309a.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 1,
    },
    {
        question: "<audio controls><source src='static/beethoven_les_adieux_1_format0.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 1,
    },
    {
        question: "<audio controls><source src='static/appass_3_format0.mp3' /></audio>",
        choice1: "Human",
        choice2: "AI",
        answer: 1,
    }
]

const SCORE_POINTS = 100
const MAX_QUESTIONS = 10

startGame = () => {
    questionCounter = 0
    score = 0
    availableQuestions = [...questions]
    getNewQuestion()
}

getNewQuestion = () => {
    
    if(availableQuestions.length === 0 || questionCounter > MAX_QUESTIONS) {
        localStorage.setItem('mostRecentScore', score)
        return window.location.assign('/final')
    } 

    questionCounter++
    progressText.innerText = `Question ${questionCounter} of ${MAX_QUESTIONS}`
    progressBarFull.style.width = `${(questionCounter/MAX_QUESTIONS)*100}%`

    const questionsIndex = Math.floor(Math.random() * availableQuestions.length)
    currentQuestion = availableQuestions[questionsIndex]
    question.innerHTML = currentQuestion.question
    
    choices.forEach(choice => {
        const number = choice.dataset['number']
        choice.innerText = currentQuestion['choice' + number]
    })

    availableQuestions.splice(questionsIndex, 1)

    acceptingAnswers = true

}

choices.forEach(choice => {
    choice.addEventListener('click', e => {
        if(!acceptingAnswers) return

        accepingAnswers = false
        const selectedChoice = e.target
        const selectedAnswer = selectedChoice.dataset['number']
        
        let classToApply = selectedAnswer == currentQuestion.answer ? 'correct' : 'incorrect'
        if (classToApply === 'correct') {
            incrementScore(SCORE_POINTS)
        }

        selectedChoice.parentElement.classList.add(classToApply)

        setTimeout(() => {
            selectedChoice.parentElement.classList.remove(classToApply)
            getNewQuestion()
        }, 1000)
    })
})

incrementScore = num => {
    score += num
    scoreText.innerText = score
}

startGame()
