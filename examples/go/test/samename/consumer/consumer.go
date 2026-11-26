package consumer

import (
	internal "example.com/samename/internal/language"
	"example.com/samename/language"
)

func Greeting() string {
	return "hello " + language.Default() + " " + internal.Tag()
}
