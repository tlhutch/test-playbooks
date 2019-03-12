# How to look up tower-qa AMIs

## RHEL images

1. Open http://amis.app.eng.bos.redhat.com/images (requires VPN access)
2. For region, select `us-east-1`
3. For products, select an `HVM_GA` image that does _not_ include `HOURLY` in its name (Amazon adds an extra charge for these images).
4. When the page updates with a filtered list of images, find an image whose Variant is listed as `RHEL-EBS Image`.
5. If multiple images all the criteria given so far:
    6. Open the [EC2 console](https://console.aws.amazon.com/ec2/)
    7. On the menu at left, under IMAGES, click on AMIs
    8. To the left of the search bar is a drop-down menu. Select Private images.
    9. For each image, do a search using the AMI id (e.g. ami-0d70a070)
    10. Compare the dates listed in the AMI Name of each image. Use the most recent image.

## Non-RHEL images

The images in tower-qa have already been vetted to ensure that they come from an official source and are not images contributed by the community. One easy way to find a new image is to look up the owner of an image we currently use, search for all images created by that owner, and locate a newer version of the image.

1. Find an existing AMI in `playbooks/images-ec2.yml` that has the platform you're looking up. Copy the ami id (e.g. ami-077b0e78)
2. Open console.aws.amazon.com
2. Click on Services -> EC2
3. Under Images, click on AMIs
5. In the AMI search bar, select Public images from the drop-down to the left of the search area.
6. Do a search using the ami id.
7. Select the image that is listed in the results. In the bottom pane, under Details, copy the Owner id (e.g. 679593333241)
8. Do a new search by owner - `Owner : 679593333241` (note: the space after Owner is required)
9. Sort the list by AMI Name. Find the OS version needed.


Note: Oracle Owner ID is 131827586825

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Aug 27, 2018.
