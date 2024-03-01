


async function deleting(event) {
    console.log(event);
    console.log("deleting");
    
    if(event.id === "delete") {

        // const postName = document.getElementById("articleTitle");
        // const deletePost = document.getElementById("delete");
        // console.log(deletePost.className);
        // console.log(postName.innerText);
        
        const listOfPost = document.getElementById("pure-g")

        for(let i = 0; i < listOfPost.children.length; i++) {
            if(listOfPost.children[i].children[0].children[0].children[0].innerText == event.className) {
                console.log("matches");
                sendBack = {
                    title : listOfPost.children[i].children[0].children[0].children[0].innerText
                }
        
                // console.log('/article/' + modified_title)
                const response = await fetch("/delete", {
                    method : "DELETE",
                    headers : {
                        "Content-Type" : "application/json"
                    },
                    body : JSON.stringify(sendBack)
                });
            
                if(response.ok) {
                    console.log(response.status)
                    // response holds get request from redirect
                    window.location.href = "/myaccount"; 
                }     
                else {
                    console.log(response.status)
                }
            }
        }
    }

};
