// console.log(sha256('The quick brown fox jumps over the lazy dog'));
// console.log(document.cookie)

window.onload = function() {
    try{
        emailValidationButton = document.getElementById('emailValidationButton')
        emailValidationButton.onclick = async function() {
            // document.getElementById('emailValidationButton').onclick = async function() {
                if (!profileViewDataJson.tmp_token || emailValidationButton.classList.contains('button-inactive')){
                    return
                }
                let location, url, settings
                location = window.location.hostname;
                // url = `http://${location}:5000/api/validation-email/`
                url = `https://${location}/api/validation-email/`
                settings = {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        "token":profileViewDataJson.tmp_token
                    })
                }
                emailValidationButton.classList.remove("button-active");
                emailValidationButton.classList.add("button-inactive");
                emailValidationButton.innerText = "🗘"
                fetch(url,settings)
                .then(res => {
                    return res.json()
                })
                .then(data => {
                    // console.log(data)
                    // console.log( data["email sent"] )
                    if (data["emailSentStatus"]){
                        emailValidationButton.innerText = "Email sent!"
                    }else{
                        emailValidationButton.innerText = "something went wrong.. try to refresh the page and click again"
                    }
                    
                })
                .catch(error => {
                    // console.log('ERROR')
                    // console.log( data )
                    emailValidationButton.innerText = "something went wrong.. try to refresh the page and click again"
                })
            };
    }catch{
        return
    }
};

const activeChecks = document.querySelectorAll('[submit-activeCheck]')
const deactiveChecks = document.querySelectorAll('[submit-deactiveAfterCheck]')
const expands = document.querySelectorAll('[submit-expand]')
const types = document.querySelectorAll('[submit-type]')
const bins = document.querySelectorAll('[submit-bin]')
const saveButton = document.getElementById('saveButtonId')
const perCents = document.querySelectorAll(['onload-perCent'])


types.forEach(ddlist => {
    ddlist.addEventListener('click', () => {
        var index = ddlist.id.match( /\d+/g ).join('')
        // console.log(index)
        // console.log(ddlist.value)
        var targetId=`${index}_perCent`
        let targetElement = document.getElementById(targetId)
        if (ddlist.value.indexOf('price') == -1){
            targetElement.classList.add('hidden')
        }else{
            targetElement.classList.remove('hidden')
        }
        saveButton.classList.remove('hidden')
    })
})

activeChecks.forEach(checkbox => {
    checkbox.addEventListener('click', () => {
        var index = checkbox.id.match( /\d+/g ).join('')
        var targetId=`${index}_status`
        let targetElement = document.getElementById(targetId)
        if (checkbox.checked){
            targetElement.innerText = '🟩'
        }else{
            targetElement.innerText = '🟥'
        }
        saveButton.classList.remove('hidden')
    })
})
deactiveChecks.forEach(checkbox => {
    checkbox.addEventListener('click', () => {
        saveButton.classList.remove('hidden')
    })
})

expands.forEach(expand => {
    expand.addEventListener('click', () => {
        var index = expand.id.match( /\d+/g ).join('')
        var targetId=`${index}_settings`
        let targetElement = document.getElementById(targetId)
        if (expand.innerText == "ᐯ"){ //ᐱ
            targetElement.classList.remove('hidden')
            expand.innerText = 'ᐱ'
        }else{
            targetElement.classList.add('hidden')
            expand.innerText = 'ᐯ'
        }
    })
})
bins.forEach(bin => {
    bin.addEventListener('click', () => {
        var index = bin.id.match( /\d+/g ).join('')
        document.getElementById(`${index}_settings`).classList.add('hidden')
        document.getElementById(`${index}_alertLine`).classList.add('hidden')
        saveButton.classList.remove('hidden')
    })
})

function deleteProfileSubmit(){
    
    if (confirm("Are you sure you want to delete your profile?")) {
        window.location.replace("/profile?deleteProfile=execute");
    }
}
function logoutProfileSubmit(){
    window.location.replace("/profile?logoutProfile=execute");
}

async function alertSubmit(){
    let data = []
    let productID, active, deactivate_after_alert, type, percentage
    for(var i = 0;i < 1000;i++){
        productID = document.getElementById(i + "_productID")
        if (!productID){
            break
        }
        if (document.getElementById(`${i}_alertLine`).classList.contains('hidden')){
            continue
        }
        productID = productID.getAttribute('productid')

        type = document.getElementById(i + "_type")
        type = type.value
        
        percentage = document.getElementById(i + "_perCent")
        percentage = percentage.value

        active = document.getElementById(i + "_activeCheck")
        active = active.checked
        
        deactivate_after_alert = document.getElementById(i + "_deactiveAfterCheck")
        deactivate_after_alert = deactivate_after_alert.checked
        data.push({
            "productID":productID,
            "type":type,
            "percentage":parseInt(percentage),
            "active":active,
            "deactivate_after_alert":deactivate_after_alert,
        })
    }
    console.log(data)

    if (profileViewDataJson['tmp_token']){
        let localLocation, url, settings
        localLocation = window.location.hostname;
        // url = `http://${localLocation}:5000/api/submitAlerts/`
        url = `https://${localLocation}/api/submitAlerts/`
        settings = {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "token":profileViewDataJson.tmp_token,
                "alerts":data
            })
        }
        try{
            saveButton.innerText = "🗘"
            const response = await fetch(url,settings)
            const jsonResp = await response.json()
            if (jsonResp.submitAlertsStatus){
                location.reload();
            }
        }catch{
            saveButton.innerText = "something went wrong.. try to refresh the page"
        }
    }else{
        saveButton.innerText = "something went wrong.. try to refresh the page"
    }
    // location.reload();
}
