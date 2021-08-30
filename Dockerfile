FROM registry.gitlab.com/gitlab-org/terraform-images/stable:latest
RUN apk --update-cache add \
    py3-pip
