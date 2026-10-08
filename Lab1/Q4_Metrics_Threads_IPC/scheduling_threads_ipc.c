#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/wait.h>
#include <string.h>

static void *worker(void *argument)
{
    const char *name = argument;

    for (int i = 1; i <= 3; ++i) {
        printf("%s: step %d\n", name, i);
    }

    return NULL;
}

int main(void)
{
    pthread_t first;
    pthread_t second;

    const char *first_name = "Thread-1";
    const char *second_name = "Thread-2";

    if (pthread_create(
            &first,
            NULL,
            worker,
            (void *)first_name) != 0)
    {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    if (pthread_create(
            &second,
            NULL,
            worker,
            (void *)second_name) != 0)
    {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    pthread_join(first, NULL);
    pthread_join(second, NULL);

    int pipefd[2];

    if (pipe(pipefd) == -1)
    {
        perror("pipe");
        return EXIT_FAILURE;
    }

    pid_t child = fork();

    if (child == -1)
    {
        perror("fork");
        return EXIT_FAILURE;
    }

    if (child == 0)
    {
        close(pipefd[1]);

        char buffer[128];

        ssize_t count = read(
            pipefd[0],
            buffer,
            sizeof(buffer) - 1
        );

        if (count == -1)
        {
            perror("read");
            close(pipefd[0]);
            _exit(EXIT_FAILURE);
        }

        buffer[count] = '\0';

        printf("Child received: %s\n", buffer);

        close(pipefd[0]);

        _exit(EXIT_SUCCESS);
    }

    close(pipefd[0]);

    const char *message =
        "Message from parent process";

    if (write(
            pipefd[1],
            message,
            strlen(message)) == -1)
    {
        perror("write");
        close(pipefd[1]);
        return EXIT_FAILURE;
    }

    close(pipefd[1]);

    waitpid(child, NULL, 0);

    printf(
        "Threads and pipe demonstration completed.\n"
    );

    return EXIT_SUCCESS;
}