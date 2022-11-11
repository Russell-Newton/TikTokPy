from typing import Optional, Union

from tiktokapipy.models import CamelCaseModel


class ShareInfo(CamelCaseModel):
    url: str
    acl: dict
    desc: str
    title: str


class Comment(CamelCaseModel):
    ############################
    # Content and interactions #
    ############################
    user: "Union[User, str]"
    text: str
    digg_count: int
    # user_digged: int            # liked by you
    reply_comment_total: Optional[int]
    author_pin: Optional[bool]  # pinned by author
    is_author_digged: bool  # liked by author
    comment_language: str

    ##################
    # Identification #
    ##################
    id: int
    # share_info: ShareInfo   # contains link to video and some extra information
    aweme_id: int  # id of video this comment is under
    reply_id: int
    reply_to_reply_id: int

    #################################################
    # Misc fields (not sure what most of these are) #
    #################################################
    create_time: int
    # status: int
    # text_extra: list
    # stick_position: int
    # user_buried: bool
    # no_show: bool
    # collect_stat: int
    # trans_btn_style: int
    # label_list: Optional[list]


from tiktokapipy.models.user import User  # noqa E402

Comment.update_forward_refs()
