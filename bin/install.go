package main

import (
	"io"
	"log"
	"os"
)

func CopyFile(filePath, dstDir string) (err error) {
	var (
		source      *os.File
		destination *os.File
	)
	if source, err = os.Open(filePath); err != nil {
		return err
	}
	defer source.Close()

	if destination, err = os.Create(dstDir); err != nil {
		return err
	}
	defer destination.Close()

	if _, err = io.Copy(destination, source); err != nil {
		return err
	}

	return err
}

func main() {
	var (
		err          error
		i3BlocksFile string = "../.config/i3/i3blocks.conf"
		i3ConfigFile string = "../.config/i3/config"
		zshrcFile    string = "../.zshrc"
		tmuxFile     string = "../.tmux.conf"
	)

	if err = CopyFile(i3ConfigFile, "~/.config/i3/config"); err != nil {
		log.Fatal("Error:", err)
	}
	if err = CopyFile(i3BlocksFile, "~/.config/i3/i3blocks.conf"); err != nil {
		log.Fatal("Error:", err)
	}
	if err = CopyFile(zshrcFile, "~/.zshrc"); err != nil {
		log.Fatal("Error:", err)
	}
	if err = CopyFile(tmuxFile, "~/.tmux.conf"); err != nil {
		log.Fatal("Error:", err)
	}
}
