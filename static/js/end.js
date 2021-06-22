const username = document.querySelector('#username')
const saveScoreBtn = document.querySelector('#save-btn')
const mostRecentScore = localStorage.getItem('mostRecentScore')

document.getElementById("score").value = mostRecentScore

username.addEventListener('keyup',() => {
    if (username.value == "") {
        saveScoreBtn.disabled = true
    }
    else {
        saveScoreBtn.disabled = false
    }
} )
