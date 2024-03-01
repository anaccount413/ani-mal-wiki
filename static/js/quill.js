
const toolbarContainer = [
    [{'header': ['2',false]}],
    [{'font': []}],
    [{'size' : ['small', false, 'large', 'huge'] }],
    [{'color': []}, {'background' : []}],
    ['bold', 'italic', 'underline', 'strike'],
    [{'align': ['', 'center', 'right', 'justify']}],
    [{'list': 'ordered'}, {'list': 'bullet'}],
    [{ 'script': 'sub'}, { 'script': 'super' }],
    ['clean'],
    
];

const quill = new Quill("#editor", {
    modules : {
        toolbar: toolbarContainer
    }, 
    theme : "snow",
    placeholder : "type here...",
    
});

let limit = 5000;
quill.on('text-change', function() {
    if (quill.getLength() > limit) {
        quill.deleteText(limit, quill.getLength());
    }
});



async function sendInformationToPython() {


    const originalString = "some string with spaces";
    const modifiedString = originalString.split(' ').join('_');

    console.log(modifiedString); // Output: some_string_with_spaces

    const quillcontent = quill.getContents();
    
    // now that they clicked publish, whatever is in the image form at the moment is what they want to send
    // if the user never added an image, it will just send as null

    let image = document.getElementById('image-upload')

    // added image requirement
    if(image.files.length === 0){
        alert('Must upload an image!')
        return;
    }
    let image_file = image.files[0]
    console.log(image_file)
    
    let title = document.getElementById("articleTitle").value;
    let modified_title = title
    // let modified_title = title.split(' ').join('_')
    let formData = new FormData()
    formData.append("title", modified_title)
    formData.append("delta", JSON.stringify(quillcontent))
    formData.append("html_content", quill.getSemanticHTML())
    formData.append("image_content", image_file)
    

    console.log('/article/' + modified_title)
    const response = await fetch("/article/" + modified_title, {
        method : "POST",
        body : formData
    });

    if(response.ok) {
        console.log(response.status)
        console.log(response)
        // response holds get request from redirect
        window.location.href = "/article/" + modified_title 
    } 

    else {
        console.log(response.status)
    }

}


document.getElementById("publish").addEventListener("click", ()=>{
    sendInformationToPython();
})


//SAVED BUTTON : 
const save = document.getElementById("save");
if(save != null) {
    save.addEventListener("click", async ()=> {
        // const html = quill.getSemanticHTML();
        // console.log(html);
        const deltaObject = quill.getContents();
        console.log(deltaObject);
        let title = document.getElementById("articleTitle").value;
        let modified_title = title.split(' ').join('_')
        let image = document.getElementById('image-upload')
        let image_file = image.files[0]

        let formData = new FormData()
        formData.append("title", modified_title)
        formData.append("delta", JSON.stringify(deltaObject))
        // formData.append("html_content", quill.getSemanticHTML())
        formData.append("image_content", image_file)

        // console.log('/article/' + modified_title)
        const response = await fetch("/save", {
            method : "POST",
            body : formData
        });
    
        if(response.ok) {
            console.log(response.status)
            console.log(response)
            // response holds get request from redirect
            window.location.href = "/myaccount/edit/" + modified_title 
        } 
    
        else {
            console.log(response.status)
        }
    })
}

//UPDATE
const update = document.getElementById("update");
if(update != null) {
    update.addEventListener("click", async ()=> {
        const deltaObject = tempQuill.getContents();
        console.log(deltaObject);

        let title = document.getElementById("articleTitle");
        console.log(title);

        let modified_title = title.split(' ').join('_')
        let image = document.getElementById('image-upload')
        let image_file = image.files[0]
        let formData = new FormData()
        formData.append("title", modified_title)
        formData.append("delta", JSON.stringify(deltaObject))
        // formData.append("html_content", quill.getSemanticHTML())
        formData.append("image_content", image_file)

        
        // console.log('/article/' + modified_title)
        const response = await fetch("/update", {
            method : "POST",
            body : formData
        });
    
        if(response.ok) {
            console.log(response.status)
            console.log(response)
            // response holds get request from redirect
            window.location.href = "/myaccount/edit/" + modified_title 
        } 
    
        else {
            console.log(response.status)
        }
    })
}


const deleting = document.getElementById("delete");
if(deleting != null) {

    deleting.addEventListener("click", async ()=>{

        const title = document.getElementById("articleTitle").value;
        console.log(title);
        const sendBack = {
            title : title,
            page : "saved"
        }

        const response = await fetch("/delete", {
            method : "DELETE",
            headers : {
                "Content-Type" : "application/json"
            },
            body : JSON.stringify(sendBack)
        });

        if(response.ok) {

            const json = await response.json();
            console.log(json);

            window.location.href = json; 

        } else {
            console.log(response.status);
        }

    })
}

