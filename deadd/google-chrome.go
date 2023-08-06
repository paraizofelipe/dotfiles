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
		AppIcon       string `json:"app-icon"`
		AppName       string `json:"app-name"`
		ImageSize     int    `json:"image-size"`
		Image         string `json:"image"`
		RemoveActions bool   `json:"remove-actions"`
		ClassName     string `json:"class-name"`
		Body          string `json:"body"`
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
	var (
		err         error
		currentPath string
		tmpPath     string = fmt.Sprintf("/tmp/%s", imageName)
	)

	if strings.Contains(originImagePath, "NamedIcon") {
		currentPath = strings.Split(originImagePath, " ")[1]
		currentPath = strings.ReplaceAll(currentPath, "\\", "")
		currentPath = strings.ReplaceAll(currentPath, "\"", "")

		if err = MoveFile(currentPath, tmpPath); err != nil {
			log.Fatal(err)
		}
		dstImagePath = fmt.Sprintf("file:///%s", tmpPath)
	}

	return
}

func buildOutput(input Input, imageName string) (err error, output Output) {
	if err, output.Modify.Body = clearString(output.Modify.Body); err != nil {
		log.Fatal(err)
	}
	output.Modify.Body = strings.TrimRight(input.Body, input.Body[:60])

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

	err = json.Unmarshal([]byte(strJson), &input)
	if err != nil {
		log.Fatal(err)
		return
	}

	// Google Mail
	if strings.Contains(input.Body, "mail.google.com") && strings.Contains(input.Body, "href") {
		if err, output = buildOutput(input, "google-mail.png"); err != nil {
			log.Fatal(err)
		}
	}

	// Google Calendar
	if strings.Contains(input.Body, "calendar.google.com") && strings.Contains(input.Body, "href") {
		if err, output = buildOutput(input, "google-calendar.png"); err != nil {
			log.Fatal(err)
		}
	}

	// Google Meet
	if strings.Contains(input.Body, "meet.google.com") && strings.Contains(input.Body, "href") {
		if err, output = buildOutput(input, "google-meet.png"); err != nil {
			log.Fatal(err)
		}
	}

	fmt.Println(output)
}
