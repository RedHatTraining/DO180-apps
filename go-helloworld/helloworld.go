package main

import (
	"fmt"
	"net/http"
)

func index_handler(w http.ResponseWriter, r *http.Request){
	fmt.Fprintf(w, "Hello, World!")
}

func main(){
	http.HandleFunc("/", index_handler)
	http.ListenAndServe(":8000", nil)
}
