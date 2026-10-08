#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <string.h>

static void file_demo(void)
{
    const char *name = "process_output.txt";
    const char *text = "Created by child process.\n";

    int fd = open(name, O_CREAT | O_WRONLY | O_TRUNC, 0640);

    if (fd == -1) {
        perror("open");
        return;
    }

    ssize_t written = write(fd, text, strlen(text));

    if (written == -1) {
        perror("write");
        close(fd);
        return;
    }

    if (close(fd) == -1) {
        perror("close");
        return;
    }

    fd = open(name, O_RDONLY);

    if (fd == -1) {
        perror("open for read");
        return;
    }

    char buffer[128];

    ssize_t count = read(fd, buffer, sizeof(buffer) - 1);

    if (count == -1) {
        perror("read");
        close(fd);
        return;
    }

    buffer[count] = '\0';

    printf("File content: %s", buffer);

    close(fd);
}

int main(void)
{
    printf("Parent PID=%ld, PPID=%ld\n",
           (long)getpid(), (long)getppid());

    pid_t child = fork();

    if (child == -1) {
        perror("fork");
        return EXIT_FAILURE;
    }

    if (child == 0) {

        printf("Child PID=%ld, PPID=%ld\n",
               (long)getpid(), (long)getppid());

        file_demo();

        printf("Child executing ls -l\n");

        execlp("ls", "ls", "-l", (char *)NULL);

        perror("execlp");
        exit(EXIT_FAILURE);
    }

    int status = 0;

    pid_t finished = waitpid(child, &status, 0);

    if (finished == -1) {
        perror("waitpid");
        return EXIT_FAILURE;
    }

    if (WIFEXITED(status)) {
        printf("Child %ld exited with status %d\n",
               (long)finished,
               WEXITSTATUS(status));
    }

    return EXIT_SUCCESS;
}