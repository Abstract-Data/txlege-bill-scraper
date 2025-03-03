from sqlmodel import JSON, Relationship
from sqlmodel import Field as SQLModelField
from typing import Dict, Optional, List
from pydantic import model_validator, HttpUrl

from .bases import TexasLegislatureModelBase
from protocols import ChamberTuple, HttpsValidatedURL

class MemberBillTypeURLs(TexasLegislatureModelBase):
    authored_url: Optional[HttpsValidatedURL] = None
    sponsored_url: Optional[HttpsValidatedURL] = None
    coauthored_url: Optional[HttpsValidatedURL] = None
    cosponsored_url: Optional[HttpsValidatedURL] = None
    amendments_authored_url: Optional[HttpsValidatedURL] = None

class MemberAddress(TexasLegislatureModelBase):
    id: Optional[int] = None
    member_id: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    phone: Optional[str] = None

class MemberDetails(TexasLegislatureModelBase):
    id: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    member_url: Optional[HttpsValidatedURL] = None
    member_session_id: Optional[str] = None
    member_district: Optional[str] = None
    member_capitol_office: Optional[str] = None
    capitol_address: Optional[MemberAddress] = None
    district_address: Optional[MemberAddress] = None
    bill_urls: Optional[MemberBillTypeURLs] = None
    bills: Dict[str, Dict] = SQLModelField(default_factory=dict)
    # member_capitol_address1: Optional[str] = None
    # member_capitol_address2: Optional[str] = None
    # member_capitol_phone: Optional[str] = None
    # member_district_address1: Optional[str] = None
    # member_district_address2: Optional[str] = None
    # member_district_phone: Optional[str] = None