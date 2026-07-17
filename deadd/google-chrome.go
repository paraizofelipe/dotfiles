package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"regexp"
	"strings"
)

func init() {
	logFile, err := os.OpenFile("/tmp/deadd-chrome-debug.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err == nil {
		log.SetOutput(logFile)
	}
}

const APP_ICON_NAME string = "google-chrome"
const IMAGE_SIZE int = 70

type Input struct {
	ActionIcons   bool   `json:"actionIcons,omitempty"`
	Actions       []any  `json:"actions,omitempty"`
	AppName       string `json:"appname,omitempty"`
	Body          string `json:"body"`
	Icon          string `json:"icon,omitempty"`
	ID            int    `json:"id,omitempty"`
	Image         string `json:"image,omitempty"`
	ImageSize     int    `json:"imageSize,omitempty"`
	Percentage    any    `json:"percentage,omitempty"`
	RepID         int    `json:"repId,omitempty"`
	Right         any    `json:"right,omitempty"`
	SendClosedMsg bool   `json:"sendClosedMsg,omitempty"`
	Time          string `json:"time,omitempty"`
	Timeout       int    `json:"timeout,omitempty"`
	Title         string `json:"title,omitempty"`
	Top           any    `json:"top,omitempty"`
	Transient     bool   `json:"transient,omitempty"`
}

type Output struct {
	Modify struct {
		AppIcon       string `json:"app-icon,omitempty"`
		AppName       string `json:"app-name,omitempty"`
		ImageSize     int    `json:"image-size,omitempty"`
		Image         string `json:"image,omitempty"`
		RemoveActions bool   `json:"remove-actions,omitempty"`
		ClassName     string `json:"class-name,omitempty"`
		Body          string `json:"body,omitempty"`
	} `json:"modify"`
	Match struct {
	} `json:"match"`
}

func (s Input) String() string {
	b, err := json.Marshal(s)
	if err != nil {
		return ""
	}
	return string(b)
}

func (s Output) String() string {
	b, err := json.Marshal(s)
	if err != nil {
		return ""
	}
	return string(b)
}

func MoveFile(sourcePath, destPath string) error {
	inputFile, err := os.Open(sourcePath)
	if err != nil {
		return err
	}
	outputFile, err := os.Create(destPath)
	if err != nil {
		inputFile.Close()
		return err
	}
	defer outputFile.Close()
	_, err = io.Copy(outputFile, inputFile)
	inputFile.Close()
	if err != nil {
		return err
	}
	return nil
}

func clearString(str string) (err error, r string) {
	regex := regexp.MustCompile(`[\n\t\\"]`)
	return nil, regex.ReplaceAllString(str, "")
}

func handlerImage(originImagePath string, imageName string) (dstImagePath string) {
	var currentPath string
	tmpPath := fmt.Sprintf("/tmp/%s", imageName)

	switch {
	case strings.HasPrefix(originImagePath, "NamedIcon"):
		parts := strings.SplitN(originImagePath, " ", 2)
		if len(parts) < 2 {
			return
		}
		currentPath = strings.ReplaceAll(strings.ReplaceAll(parts[1], "\\", ""), "\"", "")

	case strings.HasPrefix(originImagePath, "FilePath"):
		parts := strings.SplitN(originImagePath, " ", 2)
		if len(parts) < 2 {
			return
		}
		currentPath = strings.TrimSpace(strings.ReplaceAll(parts[1], "\"", ""))

	case strings.HasPrefix(originImagePath, "/"):
		currentPath = originImagePath

	case strings.HasPrefix(originImagePath, "file:///"):
		dstImagePath = originImagePath
		return
	}

	if currentPath == "" {
		return
	}

	if err := MoveFile(currentPath, tmpPath); err != nil {
		log.Printf("ERROR moving image %s -> %s: %v", currentPath, tmpPath, err)
		return
	}
	dstImagePath = fmt.Sprintf("file:///%s", tmpPath)
	return
}

func buildOutput(input Input, imageName string) (err error, output Output) {
	// Removido: truncagem do body
	// Mantém body original completo para exibir no notification center

	output.Modify.ImageSize = IMAGE_SIZE
	output.Modify.AppIcon = APP_ICON_NAME
	output.Modify.AppName = input.AppName
	output.Modify.RemoveActions = true
	output.Modify.ClassName = "GoogleMeet"
	output.Modify.Image = handlerImage(input.Image, imageName)

	return
}

func main() {
	var (
		err     error
		strJson string
		input   Input
		output  Output
	)

	reader := bufio.NewReader(os.Stdin)
	strJson, err = reader.ReadString('\n')
	if err != nil {
		log.Fatal(err)
		return
	}

	strJson = strings.ReplaceAll(strJson, "\\\\", "\\")

	log.Printf("INPUT: %s\n", strJson)

	err = json.Unmarshal([]byte(strJson), &input)
	if err != nil {
		log.Fatal(err)
		return
	}

	log.Printf("IMAGE FIELD: %s\n", input.Image)

	imageName := "google-chrome-notification.png"
	switch {
	case strings.Contains(input.Body, "mail.google.com"):
		imageName = "google-mail.png"
	case strings.Contains(input.Body, "calendar.google.com"):
		imageName = "google-calendar.png"
	case strings.Contains(input.Body, "meet.google.com"):
		imageName = "google-meet.png"
	case strings.Contains(input.Body, "chat.google.com"):
		imageName = "google-chat.png"
	}

	if err, output = buildOutput(input, imageName); err != nil {
		log.Fatal(err)
	}

	fmt.Println(output)
}
