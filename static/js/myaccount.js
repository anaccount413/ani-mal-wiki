

async function getMyAccountArticles() {

    const response = await fetch("/myaccount/data", {method : "GET"});

    if(response.ok) {
        const data = await response.json();

        console.log(data);

        if(data.length > 0) {

            const allPostDiv = document.getElementById("listOfPost")
            for(let i = 0; i < data.length; i++) {
                const postDiv = document.createElement("div");
                postDiv.className = "post";

                const buttonDiv = document.createElement("div");
                buttonDiv.className = "buttondiv";

                const editButton = document.createElement("input");
                const deleteButton = document.createElement("input");

                const redirect = document.createElement("a");

                editButton.value = "Edit";
                editButton.type = "button";
                editButton.id = "editButton";

                redirect.href = "/myaccount/page/" + data[i].title;
                redirect.className = "redirect";

                deleteButton.value = "Delete";
                deleteButton.type = "button"

                const title = document.createElement("p");

                title.innerHTML = data[i].title;
                title.id = i;

                redirect.appendChild(editButton);

                buttonDiv.appendChild(redirect);
                buttonDiv.appendChild(deleteButton);

                postDiv.appendChild(title);
                postDiv.appendChild(buttonDiv);

                allPostDiv.appendChild(postDiv);
            }
        }


    } else {
        console.log(response.status);
    }

}


window.addEventListener("load", ()=>{
    // getMyAccountArticles();
});

const deleting = document.getElementById("delete");

if(deleting != null) {
    deleting.addEventListener("click", async ()=>{
        console.log("delete button loads");

        const title = document.getElementById("articleTitle").innerText;
        console.log(title);
        sendBack = {
            articleTitle : title,
            page : "myaccount"
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


