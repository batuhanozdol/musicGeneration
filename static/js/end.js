const username = document.querySelector('#username')
const saveScoreBtn = document.querySelector('#saveScoreBtn')
const mostRecentScore = localStorage.getItem('mostRecentScore')

document.getElementById("score").value = mostRecentScore

username.addEventListener('keyup',() => {
    saveScoreBtn.disabled = !username.value
} )
